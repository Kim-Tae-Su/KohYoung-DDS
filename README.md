# DDS 기반 제어 SW APP 간 통신 인프라 설계 및 구현

## 1. 프로젝트 개요

- 프로젝트명: DDS 기반 제어 SW APP 간 통신 인프라 설계 및 구현
- 프로젝트 소속: 고영테크놀러지
- 프로젝트 기간: 2023.06 ~ 2023.09
- 프로젝트 인원: 4명

### 프로젝트 개요
본 프로젝트는 사내 SW APP 간 통신 구조를 개선하기 위해  
DDS(Data Distribution Service) 미들웨어 기반 통신 인프라를 구축한 프로젝트이다.

기존 시스템은 기계의 기능 및 모듈별로 APP이 분리되어 있었으며,  
각 APP은 Server-Client 기반 Socket 통신으로 연결된 복잡한 구조를 가지고 있었다.

이로 인해 통신 경로 확장 시 구조 복잡도가 급격히 증가하고,  
메시지 지연, 손실, 확장성 및 유지보수 측면에서 한계가 존재하였다.

본 프로젝트에서는 DDS 미들웨어를 도입하여 APP 간 통신 구조를 단순화하고,  
Monolithic Architecture(MA)에서 Microservices Architecture(MSA)로  
시스템 구조를 전환하는 것을 목표로 하였다.


---

### DDS 개요

DDS(Data Distribution Service)는 중앙 브로커 없이 Publisher와 Subscriber가  
Topic 기반으로 직접 통신하는 분산 Pub/Sub 미들웨어이다.

DDS는 실시간 시스템을 대상으로 설계된 미들웨어로,
낮은 지연 시간, QoS(Quality of Service) 기반 데이터 전달 보장, 
그리고 느슨한 결합(Loose Coupling) 구조 등의 특징을 가진다.

---

### 시스템 아키텍처
각 APP은 DDS 미들웨어를 통해 Publisher / Subscriber 역할을 수행하며,  
중앙 브로커 없이 Topic 기반 Pub/Sub 구조로 직접 통신하도록 설계하였다.

---

### 프로젝트 목표
- Socket API 기반 복잡한 Server-Client 구조 제거
- APP 간 통신 구조 단순화 및 확장성 확보
- 실시간 제어 시스템에 적합한 저지연 통신 구조 구현
- DDS QoS 기반 안정적인 데이터 전달 환경 구축
- MA → MSA 아키텍처 전환 기반 마련

---

## 2. 담당 역할

### DDS Publisher / Subscriber 개발
- Python / C++ 기반 DDS Publisher 및 Subscriber 구현
- Topic 기반 데이터 및 제어 메시지 송수신 로직 개발

### 실시간 처리 / 비실시간 처리 분리 설계
- DDS 수신 데이터 중 실시간 제어에 필요한 데이터는 즉시 처리하도록 별도 경로로 분리
- 로그 기록 및 상태 추적을 위한 데이터는 비실시간 처리 경로로 분리하여 비동기 처리
- 실시간 처리 로직과 로그 처리 간 상호 간섭 방지

### QoS 시나리오 테스트
- 메시지 손실 및 지연 상황에 따른 QoS 설정 시나리오 테스트
- Reliable / Best-Effort, History, Deadline 등 QoS 조합 검증
- 실시간 데이터와 비실시간 데이터 특성에 맞는 QoS 정책 적용

### DDS Core 이슈 분석
- DDS 통신 과정에서 발생하는 지연 및 메시지 유실 현상 재현
- DDS Core 내부 큐 처리 및 스케줄링 동작 분석
- Core 버그 원인 분석 및 패치 방향 제안

---

## 3. 기술적 문제 및 해결

### 문제 1. 대용량 데이터 전송 시 커맨드 메시지 지연 및 유실

동일한 DDS 토픽을 통해  
대용량 데이터와 커맨드 메시지를 함께 지속적으로 발행하는 환경에서  
일부 커맨드 메시지가 지연되거나 유실되는 문제가 발생하였다.

#### 원인 분석
- 하나의 토픽에 모든 유형의 메시지를 집중시킴으로써
  - DDS 내부 큐 과부하 발생
  - 대용량 데이터가 우선 처리되며 커맨드 메시지 처리 지연
- 토픽 단위 QoS 제어의 한계 노출

---

### 해결 방법

#### 1. 토픽 분리 설계
- 데이터 성격에 따라 DDS 토픽을 분리하도록 설계 변경
  - 대용량 데이터 전송용 토픽
  - 커맨드 / 제어 메시지용 토픽
- 토픽별 독립적인 데이터 흐름 구성

이를 통해:
- 메시지 처리 지연 최소화
- 메시지 유실 방지
- 토픽별 QoS 정책의 유연한 적용 가능

---

#### 2. 토픽 처리 구조 추상화
- 토픽별 처리 로직의 확장성과 유지보수를 고려하여
  - `@abstractmethod` 기반 DDS Handler 인터페이스 정의
  - 데이터 파서(Data Parser) 인터페이스 설계
- 토픽별로 Handler 및 Parser 클래스를 상속 구현하여
  - 신규 토픽 추가 시 기존 코드 수정 최소화
  - 공통 처리 로직 재사용성 확보

---

#### 3. 병렬 수신 구조 구현
- 각 토픽의 수신 모듈을 별도 스레드로 처리
- 멀티스레딩 기반 DDS Data Collector 모듈 개발
- 토픽 간 간섭 없이 병렬 수신 가능하도록 구조 개선

---

## 3-1. DDS Communication Flow

DDS 기반 APP 간 통신 흐름은 다음과 같이 구성하였다.

1. Publisher APP에서 Topic 기반 데이터 발행
2. DDS Discovery를 통한 Publisher / Subscriber 자동 매칭
3. DDS Core에서 QoS 적용 및 데이터 라우팅
4. Subscriber 측 Listener / Thread 기반 병렬 수신 처리

---

## 4. 결과 및 성과

- DDS 통신 모듈 개선 후 **시스템 메시지 전달 지연 시간 1ms 수준으로 구현**
- 토픽 분리 설계를 통해 메시지 유실 및 지연 문제 해결
- 시스템 구성 변경 없이 신규 서비스 및 통신 경로 확장 가능
- DDS Core 안정성 개선에 기여
  - Core 버그 발견 및 내부 공유
- 전체 시스템의 모듈화 및 유지보수 효율성 향상
- 멀티스레딩 기반 수신 모듈(DDS Data Collector) 개발 및 적용

---

## 5. 사용 기술

- Language
  - Python
  - C++

- Middleware
  - DDS (Data Distribution Service)

- Architecture
  - Microservices Architecture (MSA)

- Concurrency
  - Multi-threading

- Communication
  - DDS Pub/Sub
  - QoS 기반 메시징

---

## 6. 프로젝트 의의

본 프로젝트는 단순히 통신 방식을 변경하는 수준을 넘어,  
실시간 제어 시스템에 적합한 통신 아키텍처를 재설계한 사례이다.

브로커 없는 DDS 기반 Pub/Sub 구조를 도입함으로써  
APP 간 결합도를 낮추고, 확장성과 실시간성을 동시에 확보하였다.

또한 DDS Core 이슈 분석 및 패치 제안을 통해  
미들웨어 안정성 개선에 기여하였으며,  
향후 신규 제어 APP 및 서비스 확장이 가능한  
MSA 기반 통신 인프라의 기반을 마련하였다.
