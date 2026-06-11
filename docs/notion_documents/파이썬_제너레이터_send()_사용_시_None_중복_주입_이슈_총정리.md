# 파이썬 제너레이터 send() 사용 시 None 중복 주입 이슈 총정리

파이썬의 제너레이터(Generator)에서 양방향 통신(`yield`와 `.send()`)을 사용할 때, 원치 않는 `None` 값이 주입되어 출력이 두 번씩 일어나는 두 가지 대표적인 오용 사례와 작동 원리, 그리고 올바른 해결 방법을 정리합니다.


---


## **📌 핵심 요약: 왜 None이 주입되는가?**

파이썬 제너레이터에서 `result = yield value` 문법을 사용할 때, 제너레이터를 재개(Resume)하는 방식에 따라 `result`에 전달되는 값이 달라집니다.

1. **`next(generator)`**** 호출** (또는 내부적인 `next()` 호출):
  * 제너레이터를 다음 `yield`까지 진행시킵니다.
  * 이때 `yield` 식의 결과물(`result`)로 **`None`*을 주입합니다.
  * 이는 `generator.send(None)`을 호출하는 것과 내부적으로 완전히 동일합니다.
1. **`generator.send(값)`**** 호출**:
  * 제너레이터를 다음 `yield`까지 진행시킵니다.
  * 이때 `yield` 식의 결과물(`result`)로 **사용자가 전달한 값**을 주입합니다.
따라서, **한 루프 주기 내에서 ****`next()`****와 ****`send(값)`****을 동시에 호출하면 제너레이터가 두 번 재개**되면서 한 번은 `None`, 한 번은 `값`이 각각 주입되어 출력이 중복으로 발생합니다.


---


## **❌ 이슈 사례 1: ****`while`**** 루프 내 ****`next()`****와 ****`send()`**** 혼용**


### **에러 코드**


```plain text
python

generator= create_generator()

whileTrue:
next(generator)# 1. next()로 재개 (None 주입)
    cur_temperature= random.randint(0,30)
    sensor_data= generator.send(cur_temperature)# 2. send()로 재개 (온도 주입)
    time.sleep(5)
```


### **출력 결과**


```plain text
text

"sendor": "temperature", "value": 14
"sendor": "temperature", "value": None
"sendor": "temperature", "value": 25
"sendor": "temperature", "value": None
```


### **원인 분석**

* **루프당 2회 실행**: `while` 루프 한 번 돌 때마다 `next()`와 `send()`가 각각 실행되어 제너레이터 내부 코드가 두 번 흘러갑니다.
* **None의 근원**: `next(generator)`가 호출될 때 `result` 변수에 `None`이 대입되어 출력(`"value": None`)이 일어납니다.

---


## **❌ 이슈 사례 2: ****`for`**** 루프와 ****`send()`****의 혼용**


### **에러 코드**


```plain text
python

generator= create_generator()
next(generator)# 프라이밍

for valuein generator:# 1. for 루프 진입 시 암묵적으로 next() 호출 (None 주입)
    cur_temperature= random.randint(0,30)
    sensor_data= generator.send(cur_temperature)# 2. send() 호출 (온도 주입)
    time.sleep(5)
```


### **출력 결과**


```plain text
text

"sendor": "temperature", "value": None
"sendor": "temperature", "value": 3
"sendor": "temperature", "value": None
"sendor": "temperature", "value": 17
```


### **원인 분석**

* **`for`**** 루프의 작동 원리**: `for element in generator` 문은 내부적으로 매 반복 시작마다 `next(generator)`를 호출하여 값을 꺼내옵니다.
* **중복 재개**: `for`문이 실행될 때 `next()`가 수행되어 `None`이 주입되고, 그 내부 본문에서 또 `.send(온도)`를 직접 호출함으로써 결국 한 루프에 두 번 제너레이터가 작동하게 됩니다.

---


## **💡 올바른 해결법: 단방향 vs 양방향 구분하여 사용하기**


### **1. 양방향 통신 (값을 입력하면서 진행할 때) - ****`while`**** + ****`send`**

제너레이터에 값을 입력해 주는 경우에는 `for` 루프나 `next()` 반복 호출을 피하고, **최초 1회만 프라이밍(Priming)**한 후 **`send()`****만으로 제너레이터를 구동**해야 합니다.


```plain text
python

generator= create_generator()
next(generator)# 1. 최초 프라이밍: 첫 yield 지점까지 실행을 대기시킴 (출력 없음)

whileTrue:
    cur_temperature= random.randint(0,30)
# 2. 오직 send()만 사용하여 값을 주입하고 다음 yield까지 진행시킴
    sensor_data= generator.send(cur_temperature)
    time.sleep(5)
```


### **2. 단방향 통신 (제너레이터에서 값만 가져올 때) - ****`for`**** 루프**

제너레이터 내부에서 데이터를 생성하기만 하고 외부에서 입력값을 주지 않는다면, 일반적인 `for` 루프를 사용하면 됩니다.


```plain text
python

defsimple_generator() -> Generator[int,None,None]:
    value=0
whileTrue:
yield value# 단순히 값만 밖으로 보냄
        value+=1

# next() 프라이밍도 불필요함 (for 루프가 알아서 처리)
for valin simple_generator():
print(val)
    time.sleep(1)
```

