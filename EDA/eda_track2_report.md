# Track2 데이터 EDA 리포트

생성일시: 2026-01-02 03:06:33.350243

## 1. type_name 분석

- 고유값 개수: 37
- 전체 이벤트 수: 579,306

### Top 30 type_name 빈도

| type_name | count |
|-----------|-------|
| Pass | 178,582 |
| Pass Received | 167,531 |
| Carry | 88,739 |
| Recovery | 29,713 |
| Interception | 13,852 |
| Out | 12,136 |
| Duel | 11,244 |
| Clearance | 9,847 |
| Tackle | 9,498 |
| Intervention | 8,835 |
| Throw-In | 7,461 |
| Block | 6,881 |
| Cross | 6,163 |
| Shot | 4,381 |
| Pass_Freekick | 4,362 |
| Foul | 4,097 |
| Goal Kick | 3,030 |
| Error | 2,587 |
| Ball Received | 1,743 |
| Pass_Corner | 1,729 |
| Take-On | 1,456 |
| Catch | 1,109 |
| Parry | 807 |
| Aerial Clearance | 600 |
| Hit | 581 |
| Offside | 529 |
| Goal | 515 |
| Pause | 410 |
| Defensive Line Support | 320 |
| Handball_Foul | 152 |

## 2. result_name 분석

### 분포

| result_name | count |
|-------------|-------|
| Successful | 183,372 |
| Unsuccessful | 41,073 |
| Off Target | 1,970 |
| On Target | 1,117 |
| Blocked | 859 |
| Yellow_Card | 640 |
| Goal | 515 |
| Low Quality Shot | 105 |
| Direct_Red_Card | 22 |
| Keeper Rush-Out | 18 |
| Second_Yellow_Card | 11 |

- 빈 문자열: 0
- NULL: 349,604

### Top 10 type_name별 result_name 교차표

#### Pass

| result_name | count |
|-------------|-------|
| Successful | 154,195 |
| Unsuccessful | 24,387 |

#### Pass Received

| result_name | count |
|-------------|-------|

#### Carry

| result_name | count |
|-------------|-------|

#### Recovery

| result_name | count |
|-------------|-------|

#### Interception

| result_name | count |
|-------------|-------|

#### Out

| result_name | count |
|-------------|-------|

#### Duel

| result_name | count |
|-------------|-------|
| Successful | 11,239 |
| Unsuccessful | 5 |

#### Clearance

| result_name | count |
|-------------|-------|

#### Tackle

| result_name | count |
|-------------|-------|
| Unsuccessful | 6,517 |
| Successful | 2,981 |

#### Intervention

| result_name | count |
|-------------|-------|

## 3. 좌표 분석

### start_x

- Min: 0.0
- Max: 105.0
- Mean: 52.79
- 결측률: 0.00%
- 0 값 개수: 1,705

#### Quantiles

- 1%: 2.504871075
- 5%: 10.3818855
- 50%: 52.748535
- 95%: 95.140255875
- 99%: 102.66375

### start_y

- Min: 0.0
- Max: 68.0
- Mean: 34.38
- 결측률: 0.00%
- 0 값 개수: 8,350

#### Quantiles

- 1%: 0.0
- 5%: 2.5255114999999972
- 50%: 34.437988000000004
- 95%: 65.6744136
- 99%: 68.0

### end_x

- Min: 0.0
- Max: 105.0
- Mean: 52.80
- 결측률: 0.00%
- 0 값 개수: 3,797

#### Quantiles

- 1%: 1.5862507500000014
- 5%: 10.0373385
- 50%: 52.7912175
- 95%: 95.542125
- 99%: 103.7568593249999

### end_y

- Min: 0.0
- Max: 68.0
- Mean: 34.39
- 결측률: 0.00%
- 0 값 개수: 6,765

#### Quantiles

- 1%: 0.0
- 5%: 2.650164000000004
- 50%: 34.40783
- 95%: 65.56649759999999
- 99%: 68.0

### 좌표 스케일 확정 근거

- end_x 최대값: 105.0
- end_x 99% quantile: 103.7568593249999
- **결론: 0~100 스케일로 보임 (피치 길이 105m 기준)**

## 4. team_id 분석

- 결측률: 0.00%
- 2팀 게임: 198
- 1팀 게임: 0
- 기타: 0
- 전체 게임 수: 198

## 5. Shot 이벤트 분석

- 전체 Shot 수: 4,381
- 전체 게임 수: 198
- 게임당 평균 Shot: 22.13

### period_id별 분포

| period_id | count |
|-----------|-------|
| 2 | 2,601 |
| 1 | 1,780 |

