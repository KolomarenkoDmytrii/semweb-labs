# Лабораторна робота №1

## Опис предметної області та джерела даних

Як предметну область вибрано відеоігри. Для моделювання предметної області було обрано такі сутності:

- Гра: `http://mygames.xyz/games`, клас — sdo:VideoGame
- Жанр: `http://mygames.xyz/genres`, клас — sdo:DefinedTerm, предикат — sdo:genre
- Ігрова платформа: `http://mygames.xyz/platforms`, клас — sdo:Thing (загальний клас для об'єктів, що не мають конкретних класів у просторі імен Scheme.org), предикат — sdo:gamePlatform
- Розробник: `http://mygames.xyz/developers`, клас — sdo:Organization, предикат — sdo:author
- Оцінка: `http://mygames.xyz/ratings`,  клас — sdo:Rating, предикат — sdo:reviewRating

Також кожна сутність має зв'язок із своєю назвою (назва гри, платформи, розробника тощо) через предикат sdo:name, окрім оцінки, яка має зв'язок зі своїм числовим значенням через предикат sdo:ratingValue.

Джерелом даних послугував чатбот ChatGPT.

## Приклади RDF-трійок

- Назва гри: `(URIRef(http://mygames.xyz/games/elden-ring), sdo:name, "Elden Ring")`
- Оцінка конкретної гри: `(URIRef(http://mygames.xyz/ratings/minecraft), sdo:ratingValue, 93)`
- Платформа, на яку гру було випущено `(URIRef(http://mygames.xyz/games/elden-ring), sdo:gamePlatform, URIRef(http://mygames.xyz/platforms/pc))`

## Turtle-файл графу і його візуалізація

Посилання: [файл](https://github.com/KolomarenkoDmytrii/semweb-labs/blob/main/Lab1/out/games.ttl)

Візуалізація: [посилання](https://github.com/KolomarenkoDmytrii/semweb-labs/blob/main/Lab1/out/rdf_graph.html)

![Візуалізація частини графу](https://github.com/KolomarenkoDmytrii/semweb-labs/blob/main/Lab1/out/graph-visualization.png?raw=true)

## SPARQL-запити

### 1. Ігри з оцінкою вище 90

```sparql
PREFIX sdo: <https://schema.org/>

SELECT ?name ?value
WHERE {
    ?game sdo:name ?name .
    ?game sdo:reviewRating ?rating .
    ?rating sdo:ratingValue ?value .
    FILTER (?value > 90)
}
ORDER BY ASC(?value)
```

Результат:

`?name` | `?value`
---- | ----
'Minecraft' | 93
'Portal 2' | 95
'Elden Ring' | 96



### 2. Ігрові платформи, на які випустили найвище оцінену гру в жанрі головоломка з її ім'ям та оцінкою


```sparql
PREFIX sdo: <https://schema.org/>

SELECT ?name ?platform_name ?rating_value
WHERE {
    ?game sdo:name ?name .

    ?game sdo:gamePlatform ?platform .
    ?platform sdo:name ?platform_name .

    ?game sdo:reviewRating ?rating .
    ?rating sdo:ratingValue ?rating_value .
    
    {
        SELECT (MAX(?puzzle_rating_value) AS ?max_rating)
        WHERE {
            ?puzzle_game sdo:reviewRating ?puzzle_rating .
            ?puzzle_rating sdo:ratingValue ?puzzle_rating_value .
            
            ?puzzle_game sdo:genre ?genre .
            ?genre sdo:name ?genre_name .

            FILTER (?genre_name = "puzzle")
        }
    }

    FILTER (?rating_value = ?max_rating)
}
```

Результат:

`?name` | `?platform_name` | `?rating_value`
---- | ---- | ----
'PC' | 'Portal 2' | 95
'PlayStation 3' | 'Portal 2' | 95
'Xbox 360' | 'Portal 2' | 95

### 3. Середня оцінка всіх ігор випущених на конкретній платформі

```sparql
PREFIX sdo: <https://schema.org/>
        
SELECT ?platform_name (AVG(?rating_value) as ?avg_rating)
WHERE {
    ?game sdo:gamePlatform ?platform .
    ?platform sdo:name ?platform_name .

    ?game sdo:reviewRating ?rating .
    ?rating sdo:ratingValue ?rating_value .
}
GROUP BY ?platform_name
```

Результат:

`?platform_name` | `?avg_rating`
---- | ----
'PC' | 80
'PlayStation 5' | 96
'Xbox Series X/S' | 96
'PlayStation' | 93
'Xbox' | 56.5
'Nintendo Switch' | 91
'PlayStation 3' | 95
'Xbox 360' | 95
'PlayStation 4' | 89
'Xbox One' | 89
'DOS' | 82

### 4. Кількість ігор по платформам

```sparql
PREFIX sdo: <https://schema.org/>
        
SELECT ?platform_name (COUNT(?game_name) as ?games_number)
WHERE {
    ?game sdo:gamePlatform ?platform .
    ?platform sdo:name ?platform_name .

    ?game sdo:name ?game_name .
}
GROUP BY ?platform_name
```

Результат:

`?platform_name` | `?games_number`
---- | ----
'PC' | 7
'PlayStation 5' | 1
'Xbox Series X/S' | 1
'PlayStation' | 1
'Xbox' | 2
'Nintendo Switch' | 2
'PlayStation 3' | 1
'Xbox 360' | 1
'PlayStation 4' | 1
'Xbox One' | 1
'DOS' | 1

### 5. Усі розобники чиї ігри виходили на консолі PlayStation

```sparql
PREFIX sdo: <https://schema.org/>

SELECT ?platform_name ?developer_name
WHERE {
    ?game sdo:gamePlatform ?platform .
    ?platform sdo:name ?platform_name .

    ?game sdo:author ?developer .
    ?developer sdo:name ?developer_name .

    FILTER REGEX(?platform_name, "^PlayStation *")
} 
```

Результат:

`?platform_name` | `?developer_name`
---- | ----
'PlayStation 5' | 'FromSoftware'
'PlayStation' | 'Mojang Studios'
'PlayStation 3' | 'Valve'
'PlayStation 4' | 'ConcernedApe'

## Зв'язок із Wikidata

Додатково сутності ігор локального графу пов'язуються з відповідними сутностями ігор з Вікіданих, звідки беруться ще й дати релізу ігор.

Відповідний SPARQL-запит отримання даних з Вікіданих:

```sparql
PREFIX sdo: <https://schema.org/>
PREFIX wikibase: <http://wikiba.se/ontology#>
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>

SELECT ?game ?cid ?date
WHERE {
    VALUES ?game_title {{ "{str(title)}" }} .

    ?game a sdo:VideoGame .
    ?game sdo:name ?game_title .

    SERVICE <https://query.wikidata.org/sparql> {
        # назва гри вставляється через форматований 
        # рядок, бо RDFLib не підтримує передання зовнішніх змінних у SERVICE-запит
        VALUES ?wikidata_title { "game name" } .
        # назва у Вікіданих є не літералом, а сутністю  
        BIND(STRLANG(STR(?wikidata_title), "en") AS ?target_title) 

        ?cid wdt:P1476 ?target_title .
        # wdt:P31 - частина чогось, wd:Q7889 - відеогра
        ?cid wdt:P31 wd:Q7889 . 
        ?cid wdt:P577 ?date FILTER(!wikibase:isSomeValue(?date)) . # check if property has some actual value
    }
}
ORDER BY ASC(?date) LIMIT 1
```

І запит на отримання найраніще випущеної гри в графі

```sparql
PREFIX sdo: <https://schema.org/>

SELECT ?title ?date
WHERE {
    ?game a sdo:VideoGame .
    ?game sdo:name ?title .
    ?game sdo:releaseDate ?date .
}
ORDER BY ASC(?date) LIMIT 1
```

Результат виконання цього запиту

`?title` | `?date`
---- | ----
'Tetris' | 1989-01-01T00:00:00+00:00

## Помилковий приклад запиту та його виправлення

Наприклад, цей запит на отримання назви найнижче оціненої гри та власне її оцінки

```sparql
PREFIX sdo: <https://schema.org/>

SELECT ?game_title ?min_rating
WHERE {
    ?game a sdo:VideoGame .
    ?game sdo:name ?game_title .
    ?game sdo:reviewRating ?min_rating FILTER(?min_rating = MIN(?min_rating))
} 
```

буде помилковим, оскільки `MIN()` це агрегуюча функція, і її не можна застосовувати поза `SELECT`.

Тому щоб порівняти значення оцінки конкретної гри з мінімальним, це мінімальне значення потрібно отримати окремо через внутрішній `SELECT`-запит.

```sparql
PREFIX sdo: <https://schema.org/>

SELECT ?game_title ?min_rating
WHERE {
    ?game a sdo:VideoGame .
    ?game sdo:name ?game_title .

    {
        SELECT (MIN(?rating) as ?min_rating)
        WHERE {
            ?game a sdo:VideoGame .
            ?game sdo:name ?rating .
        }
    }

    ?game sdo:name ?checked_rating FILTER(?checked_rating = ?min_rating) .
} 
```

## Висновки

У висновку можна сказати, що графи є хорошою структурою даних у випадку, коли між сутностями є багато семантичних зв'язків, які ще й можуть бути пов'язані в послідовність зв'язків. Потужним засобом отримання даних з графу є SPARQL, який дозволяє оперувати графами: змінювати їх, отримувати дані й створювати з отриманих даних нові графи.


## Посилання на репозиторій

https://github.com/KolomarenkoDmytrii/semweb-labs
