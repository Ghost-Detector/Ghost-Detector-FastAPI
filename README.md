# Ghost-Detector-FastAPI

## 개요
메인 서버인 ec2 서버 FE 요청에 따라 주소지를 바탕으로 귀신 존재 확률을 분석 후 결과를 ec2 서버 FE에 반환한다.

Front End: <https://github.com/Ghost-Detector/Ghost-Detector-FE>

## 기능
### 1. 주소별 귀신 존재 확률 계산
1. 사용자가 입력한 주소를 메인서버로 부터 전달받는다.
2. 모델을 통해 귀신이 존재 하는 확률을 계산
3. 결과를 메인서버에 반환한다.

## 분석 모델
### 1. 데이터셋
폐교 : https://www.data.go.kr/data/15107729/standard.do?recommendDataYn=Y#/layer_data_infomation

폐가 : https://www.data.go.kr/tcs/dss/selectDataSetList.do?dType=FILE&keyword=%EB%B9%88%EC%A7%91&operator=AND&detailKeyword=&publicDataPk=&recmSe=N&detailText=&relatedKeyword=&commaNotInData=&commaAndData=&commaOrData=&must_not=&tabId=&dataSetCoreTf=&coreDataNm=&sort=_score&relRadio=&orgFullName=&orgFilter=&org=&orgSearch=&currentPage=1&perPage=10&brm=&instt=&svcType=&kwrdArray=&extsn=&coreDataNmArray=&pblonsipScopeCode=

추모공원 : https://www.data.go.kr/data/15114135/standard.do

사망률 : https://gsis.kwdi.re.kr/statHtml/statHtml.do?orgId=338&tblId=DT_2FB0311R&conn_path=I2

해당 데이터셋은 공공데이터이며, 타입변수에 맞게 필요한 정보만 수정하여 사용되었다. 

### 2. 전처리 과정
2-0. 데이터 로드

- s3 버킷에서 4가지 데이터셋 로드
  - closed_school.csv
  - closed_house.csv
  - memorial_park.csv
  - mortality.csv

2-1. 각 데이터셋에 카운트 열 추가

- 같은 주소에 겹치는 존재 확률 근거를 카운트 하기 위함

2-2. 그룹화

- 'province', 'city', 'district'를 기준으로 각각 그룹화 후 카운트 계산

2-3. 데이터셋 병합

- 세 개의 그룹화된 데이터셋 병합

2-4. NaN 값 처리

- NaN 값 처리 (NaN은 해당 지역에서 관련 시설이 없음을 의미)

2-5. province를 기준으로 그룹화 후 die 열의 평균 계산

- 사망률 데이터는 province 변수와 die 변수가 존재 함, 사망률 평균 계산

2-6. 데이터셋 병합_2

- 마지막으로 평균 사망률 데이터셋 병합 

### 3. 확률 계산
가중치 적용 : 사망률 1점, 추모공원 1점, 폐가 4점, 폐교 4점
계산 식 : total = 사망률 * 1 + 추모공원 * 1 + 폐가 * 4 + 폐교 * 4
