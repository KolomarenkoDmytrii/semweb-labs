import json
import os
import time
import random

from ollama import chat
from json_repair import repair_json  # Автоматично виправляє обірваний JSON
from pydantic import BaseModel, Field


class Entity(BaseModel):
    name: str = Field(
        description="Назва сутності (технологія, організація, персоналія тощо)"
    )
    entity_type: str = Field(
        description="Тип сутності: Technology, Organization, Person, Location"
    )


class Fact(BaseModel):
    subject: str = Field(description="Головна сутність (Subject)")
    relation: str = Field(
        description="Зв'язок або атрибут: uses, developed_by, located_in, influences"
    )
    object: str = Field(description="Пов'язана сутність або значення (Object)")
    description: str = Field(description="Короткий контекст факту з тексту")


class ExtractionResult(BaseModel):
    facts: list[Fact] = Field(
        description="Список видобутих структурованих фактів (не менше 30 штук)"
    )


CORPUS = """
Документ 1: У 2024 році компанія EcoCity Inc. розгорнула міську мережу датчиків на базі IoT у Києві. 
Система контролює якість повітря в реальному часі. Головний інженер проєкту, Андрій Мельник, зазначив, 
що платформа працює на протоколі LoRaWAN.
Документ 2: Протокол LoRaWAN забезпечує енергоефективний зв'язок на великих відстанях. EcoCity Inc. 
співпрацює з університетом КПІ для аналізу великих масивів даних за допомогою нейромереж.
Документ 3: У Львові аналогічний проєкт реалізує стартап SmartEco, використовуючи обладнання від Cisco. 
Андрій Мельник раніше консультував SmartEco щодо архітектури мереж у 2022 році.
Документ 4: Мережі IoT генерують терабайти даних. Для їх обробки у Києві та Львові застосовують 
хмарні сервіси Amazon Web Services (AWS). AWS забезпечує високу масштабованість та безпеку.
Документ 5: Університет КПІ підписав меморандум з AWS про підготовку фахівців з хмарних технологій 
та штучного інтелекту у 2023 році. Координатором програми став професор Іван Ковальчук.
Документ 6: Системи моніторингу повітря безпосередньо впливають на зниження рівня захворюваності дихальних шляхів, 
що підтверджено дослідженнями медичного центру у Львові.
Документ 7: Cisco та EcoCity Inc. спільно розробляють нові стандарти безпеки для IoT-пристроїв. 
Технічний директор Cisco, Олена Шевченко, підкреслила важливість шифрування даних.
Документ 8: Розвиток Smart City ініціатив в Україні фінансується міжнародними фондами, зокрема 
Європейським банком реконструкції та розвитку (ЄБРР), який підтримав проєкти у Києві у 2023 році.
"""


def call_ollama_with_retry(
    api_call_func, *args, max_retries=4, initial_delay=1.0, max_delay=60.0, **kwargs
):
    delay = initial_delay
    for attempt in range(1, max_retries + 1):
        try:
            return api_call_func(*args, **kwargs)
        except Exception as e:
            if attempt == max_retries:
                raise e
            jitter = random.uniform(0, 1.0)
            sleep_time = min(delay + jitter, max_delay)
            print(
                f"[!] Помилка Ollama API: {e}. Спроба {attempt} із {max_retries}. Повтор через {sleep_time:.2f} сек..."
            )
            time.sleep(sleep_time)
            delay *= 2


def extract_knowledge():
    print("[*] Виконання LLM-екстракції фактів через Ollama (модель gemma4:e2b)...")

    json_schema = ExtractionResult.model_json_schema()
    prompt = (
        "Проаналізуй наступний корпус текстів і видобуди з нього структуровані факти. "
        "Сформуй не менше 30 детальних фактів (subject, relation, object, description), "
        "використовуючи сутності типу Technology, Organization, Person, Location та зв'язки між ними. "
        f"Відповідь поверни виключно у форматі JSON, що відповідає такій схемі: {json.dumps(json_schema, ensure_ascii=False)}\n\n"
        f"Корпус текстів:\n{CORPUS}"
    )

    def _make_call():
        response = chat(
            model="gemma4:e2b",
            messages=[{"role": "user", "content": prompt}],
            format=json_schema,
            options={
                "num_predict": 127000  # Збільшуємо ліміт токенів на відповідь, щоб JSON не обривався
            },
        )
        return response.message.content

    response_text = call_ollama_with_retry(_make_call)
    # print("[*] response_text =")
    # print(response_text)
    # print("-" * 10)

    # Безпечне декодування з можливістю автовиправлення обірваного JSON
    try:
        result_data = json.loads(response_text)
    except json.JSONDecodeError:
        print(
            "[!] Увага: JSON було обірвано. Застосовується автовиправлення (json_repair)..."
        )
        repaired_json_str = repair_json(response_text)
        result_data = json.loads(repaired_json_str)

    with open("facts.json", "w", encoding="utf-8") as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)

    print(f"[+] Екстракцію завершено. Збережено фактів у файл facts.json.")


if __name__ == "__main__":
    extract_knowledge()
