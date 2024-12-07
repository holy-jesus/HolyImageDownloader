Различные заметки, мысли, идеи.

## Идеи

Использовать https://www.google.com/advanced_image_search для поиска, так как даёт больше опций для более точного поиска.

## Заметки

### Ссылки

#### Поиск (Документ)

Пример поиска по картинке: `https://www.google.com/search?as_st=y&as_q=hello world&as_epq=&as_oq=&as_eq=&imgar=&imgcolor=&imgtype=&cr=&as_sitesearch=&as_filetype=&tbs=&udm=2`

- `as_st` - ?
- `as_q` - Текст по которому искать
- `as_epq` - ?
- `as_oq` - ?
- `as_eq` - ?
- `imgar` - ?
- `imgcolor` - Цвет картинки
- `imgtype` - Тип картинки ?
- `cr` - ?
- `as_sitesearch` - ?
- `as_filetype` - Тип файла
- `tbs` - ?
- `udm=2` - поиск картинок

За поиск по картинке отвечает udm=2

#### Дальнейшее получение картинок (JS)

Они поменяли POST запросы на GET, в итоге куча говна в query запроса.

Поменяли ли они вид возвращаемых данных - хз. Похоже на прошлый вариант.

В JS есть код для формирования body если запрос POST, но работает это или нет - хз.

Запрос делается в функции `getNextImages` (изначально GMb)

Функцию `getNextImages` вызывает функция `NMb`

Функцию `NMb` вызывает функция `Zs.fetch`

WIZ парсится в файле parsing.js на строчке ~47780

После запроса всё идёт к строчке 1215;

##### Заголовки

WIZ - заголовок

- `ejMLCd` - `X-Geo`
- `PYFuDc` - `X-Client-Data`
- `JHHKub` - `X-Client-Pctx`
- `qfI0Zc` - `X-Search-Ci-Fi`
- `AUf7qc` - `X-Silk-Capabilities`

##### Всякое важное

parsing.js `_xjs_toggles`

`_basejs`, `_basecss`, `_basecomb`: google.xjs

## Инструменты, которые я использую

- [VSCodium](https://vscodium.com/)
- [Firefox](https://www.mozilla.org/ru/firefox/new/)
- [Firefox Developer Tools](https://firefox-source-docs.mozilla.org/devtools-user/)
- [Firefox JavaScript Debugger](https://firefox-source-docs.mozilla.org/devtools-user/debugger/)
- [Анализатор HAR](https://toolbox.googleapps.com/apps/har_analyzer/)
