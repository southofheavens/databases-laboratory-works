# Лабораторная работа по предмету "Базы Данных" №1

Код для генерации датасета находится в файле gen\_dataset.py. Сгенерированный датасет необходимо поместить в папку init.  

## 1.1: Типы индексов и их использование на практике

- B-tree Index  

B-tree — это универсальный индекс, используется по умолчанию в PostgreSQL.  
Идеален для поиска по: =, >, <, BETWEEN, сортировки (ORDER BY) и фильтрации (WHERE price > 1000).  

Например:  
SELECT COUNT(\*) FROM instruments WHERE price BETWEEN 100 AND 500;   

До внедрения B-tree:  
Execution Time: 1172.367 ms  

После внедрения B-tree:  
Execution Time: 56.420 ms



- GIN Index  
GIN (Generalized Inverted Index) подходит для поиска по словам и фразам внутри текста; может индексировать массивы, чтобы быстро искать значения внутри них; подходит для работы с jsonb, особенно когда мы хотим искать по ключам и значениям.  

Например:  
SELECT \* FROM instruments WHERE to_tsvector('english', description) @@ plainto_tsquery('english', 'clarinet germany');  

До внедрения GIN:
Execution Time: 1328.875 ms  

После внедрения GIN:  
Execution Time: 84.113 ms



- BRIN Index  
BRIN (Block Range INdex) — это лёгкий и компактный индекс, который работает по диапазонам страниц в таблице.  
Эффективен для столбцов, значения которых монотонно возрастают или убывают. Предназначен для обработки очень больших таблиц.  

Например:  
SELECT \* FROM instruments WHERE instrument_id BETWEEN 1000000 AND 1500000  

До внедрения BRIN:  
Execution Time: 1400.00 ms  
  
После внедрения BRIN:  
Execution Time: 358.629 ms  

  
  
## 1.2: Транзакции в PostgreSQL: виды и использование на практике  

Попробуем создать транзакцию и поймать артефакты. Пример кода:  

```Python
import threading
import time
import psycopg2

DB_CONFIG = {
    'dbname': 'music_store',
    'user': 'postgres',
    'password': 'postgres',
    'host': 'localhost',
    'port': 5433
}

PHANTOM_NAME = "Phantom Instrument 2354"

def txn1():
    conn = psycopg2.connect(**DB_CONFIG)
    conn.set_session(isolation_level="READ COMMITTED", autocommit=False)
    cur = conn.cursor()

    print(f"[TXN1] begin")
    cur.execute("BEGIN;")

    cur.execute("SELECT COUNT(*) FROM instruments WHERE price < 100;")
    count_before = cur.fetchone()[0]
    print(f"[TXN1] before: {count_before}")

    time.sleep(5)

    cur.execute("SELECT COUNT(*) FROM instruments WHERE price < 100;")
    count_after = cur.fetchone()[0]
    print(f"[TXN1] after: {count_after}")

    conn.commit()
    print("[TXN1] commit\n")
    conn.close()

def txn2():
    time.sleep(2)

    conn = psycopg2.connect(**DB_CONFIG)
    conn.set_session(autocommit=False)
    cur = conn.cursor()

    print("[TXN2] begin")
    cur.execute("BEGIN;")

    cur.execute("""
        INSERT INTO instruments (
            name, type, family, manufacturer, origin_country,
            year_introduced, price, description
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT DO NOTHING;
    """, (
        PHANTOM_NAME,
        "Keyboard",
        "Keys",
        "GhostCorp",
        "Germany",
        2024,
        49.99,
        "Phantom insert for transaction demo"
    ))

    print("[TXN2] inserted phantom instrument")
    conn.commit()
    print("[TXN2] commit\n")
    conn.close()


def cleanup():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("DELETE FROM instruments WHERE name = %s;", (PHANTOM_NAME,))
    conn.commit()
    conn.close()
    print(f"[CLEANUP] Deleted '{PHANTOM_NAME}' from instruments\n")


if __name__ == "__main__":
    t1 = threading.Thread(target=txn1)
    t2 = threading.Thread(target=txn2)

    t1.start()
    t2.start()

    t1.join()
    t2.join()

    cleanup()
```
   
Запустим две транзакции параллельно. Одна будет считать количество элементов  
таблицы с ценой меньше 50, а вторая добавит повторный элемент во время  
работы первой. Если числа окажутся разными мы поймаем «фантомное чтение».  
При уровне изоляции Read Commited:  

[TXN1] begin  
[TXN1] before: 27398  
[TXN2] begin  
[TXN2] inserted phantom instrument  
[TXN2] commit  

[TXN1] after: 27399  
[TXN1] commit  

Артефакт пойман.   

Попробуем осуществить такую же операцию, но с уровнем изоляции Repeatable
Read:  

[TXN1] begin  
[TXN1] before: 27398  
[TXN2] begin  
[TXN2] inserted phantom instrument  
[TXN2] commit  

[TXN1] after: 27398  
[TXN1] commit  

Получается, что данный уровень изоляции защищает от фантомных чтений.  

Попробуем поймать другой артефакт – «Неповторяющееся чтение». Пример
кода:  

```Python
import threading
import time
import psycopg2

DB_CONFIG = {
    'dbname': 'music_store',
    'user': 'postgres',
    'password': 'postgres',
    'host': 'localhost',
    'port': 5433
}

INSTRUMENT_NAME = 'Some_guitar'


def insert_demo_instrument():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Вставляем инструмент
    cur.execute("""
        INSERT INTO instruments (
            name, type, family, manufacturer, origin_country,
            year_introduced, price, description
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        INSTRUMENT_NAME,
        'String',
        'Guitar',
        'DemoBrand',
        'USA',
        2020,
        10.00,
        'Temporary guitar for transaction demo'
    ))

    conn.commit()
    conn.close()
    print(f"[SETUP] Inserted '{INSTRUMENT_NAME}'")


def cleanup_demo_instrument():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    cur.execute("DELETE FROM instruments WHERE name = %s;", (INSTRUMENT_NAME,))
    conn.commit()
    conn.close()
    print(f"[CLEANUP] Deleted '{INSTRUMENT_NAME}'\n")


def txn1():
    conn = psycopg2.connect(**DB_CONFIG)
    conn.set_session(isolation_level="READ COMMITTED", autocommit=False)
    cur = conn.cursor()

    print("[TXN1] begin")
    cur.execute("BEGIN;")

    cur.execute("SELECT price FROM instruments WHERE name = %s;", (INSTRUMENT_NAME,))
    price_before = cur.fetchone()[0]
    print(f"[TXN1] before: {price_before}")

    print("[TXN1] wait")
    time.sleep(5)

    cur.execute("SELECT price FROM instruments WHERE name = %s;", (INSTRUMENT_NAME,))
    price_after = cur.fetchone()[0]
    print(f"[TXN1] after: {price_after}")

    conn.commit()
    print("[TXN1] commit\n")
    conn.close()


def txn2():
    time.sleep(2)

    conn = psycopg2.connect(**DB_CONFIG)
    conn.set_session(autocommit=False)
    cur = conn.cursor()

    print("[TXN2] begin")
    cur.execute("BEGIN;")

    cur.execute("UPDATE instruments SET price = 99.99 WHERE name = %s;", (INSTRUMENT_NAME,))
    print("[TXN2] updated price to 99.99")

    conn.commit()
    print("[TXN2] commit\n")
    conn.close()


if __name__ == "__main__":
    insert_demo_instrument()

    t1 = threading.Thread(target=txn1)
    t2 = threading.Thread(target=txn2)

    t1.start()
    t2.start()

    t1.join()
    t2.join()

    cleanup_demo_instrument()
```  

Запустим две транзации параллельно. Одна будет искать определенную гитару, а вторая изменит её цену во время выполнения первой.  
При уровне изоляции Read Commited:  

[TXN1] begin
[TXN2] begin
[TXN1] before: 10.00
[TXN1] wait
[TXN2] updated price to 99.99
[TXN2] commit

[TXN1] after: 99.99
[TXN1] commit  

Артефакт пойман.  

Повторим то же самое при уровне изоляции Repeatable Read:  

[TXN1] begin
[TXN2] begin
[TXN1] before: 10.00
[TXN1] wait
[TXN2] updated price to 99.99
[TXN2] commit

[TXN1] after: 10.00
[TXN1] commit  

Как видно, уровень изоляции Repeatable read защитил от данного артефакта.  



## 1.3: Использование расширений PostgreSQL для полнотекстового поиска и криптографических операций  

pg_trgm и pg_bigm позволяют ускорить поиск по тексту, используя триграммы и
биграммы.   
Попробуем поискать в базе данных инструменты, название которых содержит "First Guitar", но перед этим вставим запись с уникальным именем "First Guitar":  
Execution Time: 3463.170 ms
  
Попробуем применить триграммы, которые эффективны для поиска похожих
слов:  
Execution Time: 0.353 ms  
  
Теперь попробуем поискать в базе данных инструменты, тип которых содержит "another type", но перед этим вставим запись с уникальным типом "another type":
Execution Time: 0.438 ms  

Попробуем применить биграммы:  
Exectuion Time: 0.209 ms  



