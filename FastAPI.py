# main.py 파일 생성 후 아래 코드 작성
# cloud9

from fastapi import FastAPI
import pandas as pd
import boto3
import io
from fastapi.middleware.cors import CORSMiddleware

s3 = boto3.client('s3')
bucket_name = 'wku-ghost-bucket'

app = FastAPI()

origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8080",
    "file:///C:/Users/rnrrb/Desktop/Ghost-Detector-FE/index.html"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def read_csv_from_s3(file_name):
    obj = s3.get_object(Bucket=bucket_name, Key=file_name)
    test1=pd.read_csv(io.BytesIO(obj["Body"].read()))
    return test1


def calculate_probability(df, province, city, district):
    # 해당 지역의 데이터 행 찾기
    row=df[(df["province"]== province) & (df["city"]== city) & (df["district"]== district)]
    
    if len(row)==0:
        return 20000
    
    # 폐교, 폐가, 추모공원 개수 및 사망률 값을 가져옴
    school_count=row["scaled_school_count"].values[0]
    house_count=row["scaled_house_count"].values[0]
    park_count=row["scaled_park_count"].values[0]

    mortality_rate=row['die'].values[0]  
    
     # 가중치 적용: 사망률 4점, 폐교/폐가/추모공원 각각 2점
    weighted_total=mortality_rate*1+school_count*4+house_count*4+park_count*1

     # 정규화 및 퍼센트 변환: 전체 점수를 가중치 합계로 나눈 후 x100
    probability_percent=(weighted_total/10)*100
    
    return probability_percent


@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/ghost")
def calculate_percent(province: str, city: str, district:str):
    closed_school_df = read_csv_from_s3('closed_school1.csv')
    closed_house_df = read_csv_from_s3('closed_house1.csv')
    memorial_park_df = read_csv_from_s3('memorial_park1.csv')
    mortality_df = read_csv_from_s3('mortality1.csv')
    
    
    # 각 데이터 셋에 카운트 열 추가
    closed_school_df['school_count'] = 1
    closed_house_df['house_count'] = 1
    memorial_park_df['park_count'] = 1
    
    # 'province', 'city', 'district'를 기준으로 각각 그룹화 후 카운트 계산
    school_grouped = closed_school_df.groupby(['province', 'city', 'district'])['school_count'].count().reset_index()
    house_grouped = closed_house_df.groupby(['province', 'city', 'district'])['house_count'].count().reset_index()
    park_grouped = memorial_park_df.groupby(['province', 'city', 'district'])['park_count'].count().reset_index()
    
    # 세 개의 그룹화된 데이터 셋 병합
    merged_1 = pd.merge(school_grouped , house_grouped , on=['province','city','district'], how='outer')
    merged_total = pd.merge(merged_1 , park_grouped , on=['province','city','district'], how='outer')
    
    # NaN 값 처리 (NaN은 해당 지역에서 관련 시설이 없음을 의미)
    merged_total.fillna(0, inplace=True)
    
    # province를 기준으로 그룹화 후 die 열의 평균 계산
    mortality_avg= mortality_df.groupby('province')['die'].mean().reset_index()
    
    # 마지막으로 평균 사망률 데이터 셋 병합 
    final_merged_data= pd.merge(merged_total,mortality_avg,on=['province'],how='inner')
    
    for column in ['school_count', 'house_count', 'park_count']:
        min_val = final_merged_data[column].min()
        max_val = final_merged_data[column].max()
        final_merged_data[f'scaled_{column}'] =(final_merged_data[column] - min_val) / (max_val - min_val)
    
    probability_percent=calculate_probability(final_merged_data, province, city, district)
    
    return {"probability":int(probability_percent)}