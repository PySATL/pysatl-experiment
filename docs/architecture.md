# Организация проекта

```text
src/pysatl_experiment/
├── cli/                         # команды и разбор CLI-параметров
├── configuration/
│   ├── experiment_config.py     # конфигурации экспериментов
│   ├── experiment_config_interfaces.py # маркеры типов экспериментов
│   ├── raw_experiment_config.py # исходная конфигурация
│   ├── steps_config.py          # конфигурации шагов
│   ├── validation/              # схемы и проверка конфигурации
│   └── config_loader.py         # чтение raw-конфигурации из JSON
├── experiment_execution/
│   ├── build.py                 # сборка через зарегистрированные обработчики
│   ├── registry.py              # типизированная регистрация и плагины
│   ├── dependencies.py          # проверка необходимых внешних результатов
│   ├── run_preparation.py       # восстановление запуска и применение run_mode
│   ├── run_state.py             # состояние запуска, без операций с БД
│   ├── runner.py                # выполнение шагов и сохранение статусов
│   ├── configured_criterion.py  # созданный экземпляр статистического критерия
│   ├── experiment_config_adapter.py
│   ├── experiment_steps.py
│   ├── experiment_storages.py
│   ├── experiment_factory/      # создание зависимостей и сборка шагов
│   ├── planning/
│   │   ├── plan.py              # общий Generic-контейнер задач
│   │   ├── generation.py
│   │   ├── critical_value.py
│   │   ├── power.py
│   │   └── time_complexity.py
│   └── step/
│       ├── generation_step/
│       ├── execution_step/
│       └── report_step/
├── parallel/                    # универсальный Scheduler и BufferedSaver
├── persistence/
│   ├── models/                  # данные, фильтры и запросы
│   ├── contracts/               # интерфейсы хранилищ
│   ├── random_values_iterator.py
│   ├── time_complexity_iterator.py
│   └── sqlalchemy/              # ORM-модели, сессии и реализации хранилищ
├── sample_loading/              # загрузка и проверка входных выборок
├── types/                       # общие типы, включая Sample, SampleBatch и SampleSetSpec
├── utils/
│   ├── experiment_utils.py      # JSON-файлы экспериментов и загрузка выборок
│   ├── files_utils.py           # пути пользовательских файлов
│   ├── experiment_names.py      # нормализация имени эксперимента
│   └── report_utils.py          # общие операции отчётов
├── loggers/
└── resources/report_templates/
```

## Границы ответственности

`configuration` описывает настройки. `CriterionConfig` содержит код и параметры,
а `experiment_execution.configured_criterion.ConfiguredCriterion` — уже созданный
статистический критерий. Маркеры в `experiment_config_interfaces.py` сохранены.

`planning.plan` и `run_state` не импортируют фабрики, конкретные шаги или SQLAlchemy.
Планировщики отдельных видов работают с контрактами хранилищ и готовят задачи.
Фабрики создают хранилища и собирают шаги; восстановление и очистка запуска
выполняются отдельно в `run_preparation`.

`persistence.models` не содержит интерфейсов хранилищ или ORM-реализаций.
`persistence.contracts` зависит от моделей, а `persistence.sqlalchemy` реализует
контракты. `types` содержит `Sample`, `SampleBatch` и `SampleSetSpec` с проверкой
размеров и количества выборок. Эти типы используют загрузчики и вычислительные
воркеры. `sample_loading` загружает выборки по спецификации и собирает `SampleBatch`;
адаптер `sqlalchemy_source` создаёт источник в рабочем процессе.
Состояние и план стороннего эксперимента могут иметь собственные типы:
реестр связывает их с типами аргументов фабрики.

`utils.experiment_utils` отвечает за именованные JSON-файлы; `config_loader` читает
raw-документ по произвольному пути с диагностикой ошибок. Итераторы хранилищ
находятся в `persistence`, загрузка входных выборок — в `sample_loading`,
общая подготовка отчётов — в `utils/report_utils.py`.

## Тесты

Тесты конфигурационных моделей находятся в `tests/configuration`, проверки сборки
и реестра — в `tests/experiment_execution`. Его подкаталоги `experiment_factory`,
`planning`, `step` соответствуют исходникам по мере появления тестов.
Универсальный планировщик и буфер записи проверяются в `tests/parallel`.
SQLAlchemy-хранилища проверяются в `tests/persistence/sqlalchemy`, итератор выборок —
в `tests/persistence`, загрузка выборок — в `tests/sample_loading`. `tests/typing` проверяет совместимость типов расширений.

Старые модули не оставлены как совместимые обёртки. При добавлении кода следует
использовать актуальные пути импортов из структуры выше.

Идентификатор эксперимента — `experiment_name`. В таблице `experiments` имя
является первичным ключом; настройки не участвуют в идентификации. Статусы
шагов обновляются по имени. Запросы результатов power, time complexity и
critical value также включают имя, чтобы одинаковые настройки разных
экспериментов не смешивали их результаты.

Результаты critical value хранятся в локальной таблице
`experiment_limit_distributions`. Модель и контракт этого хранилища находятся
в `persistence`; кэш критических значений внешней библиотеки остаётся отдельным.

Изменение схемы требует переноса старых баз перед использованием новой версии.
`create_all` не преобразует существующие таблицы. В старой таблице `experiments`
имена не сохранялись: для переноса необходимо явно сопоставить старые записи
с именами экспериментов. Автоматическое угадывание имён и удаление старых данных
не выполняются.

`TimeComplexityExecutionStep` получает `TimeComplexityExecutionContext`, фабрику
источника выборок и хранилище результатов отдельными аргументами. Контекст содержит
имя эксперимента, число процессов и подготовленные задания `TimeComplexityTask`.
В каждом задании находятся `CriterionSpec` (разрешённый класс статистики и все
аргументы конструктора) и `SampleSetSpec`. Число повторений берётся из
`SampleSetSpec.samples_count` и не дублируется в контексте.

Планировщик разрешает классы без создания экземпляров статистик. Обработчик
задания использует источник выборок, созданный один раз для рабочего процесса,
загружает `SampleBatch`
и создаёт статистику с параметрами гипотезы и критерия. Worker измеряет только
вычисление статистики. `ParallelExecutionStep` управляет процессами и сохраняет
вернувшиеся результаты в родительском процессе. Соединения с БД и хранилище
результатов между процессами не передаются.

Каждое распределение из `generate.distributions` задаёт отдельную серию выборок.
Её `generator_code` строится из имени распределения и отсортированных имён
параметров: `normal_mean_[0.0,1.0]_var_1.0`. Числа нормализуются к `float`,
пропущенные параметры дополняются значениями генератора по умолчанию. Фиксированное
значение кодируется числом, диапазон — `[min,max]`; разные диапазоны сохраняют
разные коды даже при совпадении середин или фактически выбранных значений.

Для каждого недостающего образца параметры-диапазоны независимо выбираются
равномерно. `generator_parameters` у сохранённой выборки содержит фактические
числа, а `generator_code` — исходную спецификацию серии. `SampleSetSpec` и
`load_sample_batch` выбирают серию по коду, имени эксперимента и размеру выборки.
Подсчёт недостающих данных и очистка при `overwrite` используют тот же код.

План time complexity включает каждую комбинацию серии, критерия и размера
выборки. `generator_code` входит в модель, запрос и уникальный ключ результата
`time_complexity`; отчёт разделяет серии в подписях таблицы и графика.

Все эксперименты используют один `ReportBuildingStep`. Он получает
`ReportStepContext`, источник результатов `Iterable[ResultT]` и конкретный
`IReportBuilder[ReportBuilderContext[ResultT]]`. Контекст шага содержит только
`report_name`, `report_mode`, `results_path` и `template_path`.

Фабрика выбирает источник и построитель. `TimeComplexityResults` читает данные
через `TimeComplexityIterator` страницами (`read_batch_size=1000`), исключает
результаты вне текущей конфигурации, проверяет полноту и дубликаты и упорядочивает
данные. Для power и critical value адаптер `QueryResults` читает точные запросы
через существующий `get_data` и сообщает об отсутствующих результатах. Оба
источника создают новый обход при каждом вызове `iter`, поэтому шаг можно
запускать повторно. Сам шаг не требует от источника методов записи или bulk API.

Построитель получает `ReportBuilderContext[ResultT]` с настройками вывода и
`data: tuple[ResultT, ...]`. Чтение завершено до вызова `build(context)`;
ссылки на сторы и ленивые итераторы построителю не передаются. Пакетное чтение
ограничивает размер одной загрузки, но выбранные результаты остаются в памяти
полностью. Ошибка чтения или неполная выборка предотвращает вызов построителя.

`PowerReportBuilder` группирует исходные решения и вычисляет мощность.
`CriticalValueReportBuilder` получает эмпирические распределения и вычисляет
критические значения; уровни значимости и конфигурации критериев передаёт фабрика
при создании построителя. Каждый построитель применяет шаблон из контекста,
учитывает режим графиков и сохраняет PDF в указанную директорию.

`TimeComplexityReportBuilder` вычисляет средние, строит график, применяет шаблон
и записывает PDF. Группировка использует структурированный ключ: код критерия,
его параметры, код серии выборок и число повторений. Подписи формируются отдельно
от ключей. Шаблон получает исходные `data`, средние `report_data`, размеры `sizes`,
имя `report_name`, дату `timestamp` и необязательный график `plot_image`.
Фабрика передаёт стандартный `tc_template.html`; другой контекст может выбрать
собственный шаблон. Один построитель можно повторно использовать для разных отчётов.

Старые базы без `time_complexity.generator_code` требуют явной миграции данных
и уникального ограничения либо повторной генерации в новой базе, указанной в
`storage_connection`. Инициализация сообщает об устаревшей схеме и не меняет её.
`run_mode=overwrite` не выполняет миграцию схемы. Старые коды выборок также нужно
пересчитать по исходной конфигурации: исходный диапазон нельзя восстановить из
одного реализованного значения параметра. Старые данные автоматически не удаляются.

## Пакетное хранение

`IBulkDataStorage[Model, Filter]` наследует `IStorage` и задаёт два метода:
`bulk_insert(data, batch_size=1000)` и
`read_bulk(query, after_id=None, batch_size=1000)`. Результат чтения —
`BulkBatch[Model]` с полями `items` и `next_after_id`. Курсор — технический id
последней строки, а не номер страницы. `None` означает конец обхода; после
полной последней страницы допускается дополнительное пустое чтение.

Контракт реализуют хранилища случайных выборок и результатов времени.
`RandomValuesBatch` — типизированное имя для `BulkBatch[RandomValuesModel]`.
При переходе на этот API вызовы `read_batch` заменяются на `read_bulk`,
поле страницы `samples` — на `items`, а `bulk_insert_data` у хранилища времени —
на `bulk_insert`. Операции с одиночными результатами времени сохраняются через
`IDataStorage`; запись одной модели использует тот же пакетный механизм.

Запись потребляет входной iterable ограниченными пачками. Каждая пачка атомарна:
ошибка откатывает текущую пачку, уже записанные остаются. Случайные выборки
добавляются; результаты времени обновляются при совпадении полного ключа,
и последнее значение повторяющегося ключа побеждает.

`BulkDataIterator` лениво читает страницы, поддерживает `batch_size` и общий
`limit`. `RandomValuesIterator` и `TimeComplexityIterator` специализируют его
для своих моделей и фильтров. Во время обхода набор данных должен оставаться
неизменным; итератор не создаёт снимок всей базы.

```python
from pysatl_experiment.persistence.models.time_complexity import TimeComplexityFilter
from pysatl_experiment.persistence.time_complexity_iterator import TimeComplexityIterator

storage.bulk_insert(measurements, batch_size=100)
query = TimeComplexityFilter(experiment_name="experiment-a", criterion_code="KS")
for measurement in TimeComplexityIterator(storage, query, batch_size=100):
    process(measurement)
```


## Параллельное выполнение

`pysatl_experiment.parallel.Scheduler` не зависит от экспериментов, моделей
хранения или SQLAlchemy. Задание — функция или объект с методом
`__call__(context)`, возвращающий произвольный результат, в том числе `None`.
`context_factory` вызывается один раз для каждого запущенного исполнителя;
контекст переиспользуется между заданиями и повторными вызовами `run` в том же
пуле. При новом запуске пула создаются новые контексты.

По умолчанию используются процессы (`backend="process"`) с методом запуска
`spawn`; `backend="thread"` выбирает потоки. Для процессов задания, фабрика и
результаты должны поддерживать pickle. Контекст создаётся внутри исполнителя
и не сериализуется: в нём можно держать хранилище, фабрику сессий или клиент.
Операции хранилища отвечают за закрытие сессий и границы транзакций. Подготовку
схемы БД следует завершить до старта параллельных заданий.

`iterate_results` лениво принимает iterable и отдаёт результаты по готовности.
`max_pending` ограничивает число отправленных, но ещё не переданных потребителю
задач; по умолчанию это `2 * max_workers`. Ограничение применяется к каждому
вызову `iterate_results`; отдельные вызовы `submit` им не ограничиваются.
`run` собирает результаты в список. `submit` возвращает типизированный `Future`.
Для досрочного прекращения обхода нужно закрыть итератор (например,
`contextlib.closing`): ожидающие задачи отменяются по возможности, уже работающие
могут завершиться. Ошибки задачи, входного iterable и инициализации передаются
вызывающему коду. Выход из `with` дожидается работающих задач.

```python
from dataclasses import dataclass
from pysatl_experiment.parallel import Scheduler, no_context


@dataclass(frozen=True)
class Square:
    value: int

    def __call__(self, context: None) -> int:
        return self.value ** 2


if __name__ == "__main__":
    with Scheduler(max_workers=4, context_factory=no_context) as scheduler:
        for result in scheduler.iterate_results(Square(i) for i in range(100)):
            print(result)
```

Для заданий с БД фабрика создаёт хранилище внутри исполнителя:

```python
from functools import partial
from pysatl_experiment.parallel import Scheduler
from pysatl_experiment.persistence.models.random_values import RandomValuesFilter
from pysatl_experiment.persistence.sqlalchemy.random_values import AlchemyRandomValuesStorage


def open_storage(connection: str) -> AlchemyRandomValuesStorage:
    storage = AlchemyRandomValuesStorage(connection)
    storage.init()
    return storage


def count_samples(experiment: str, storage: AlchemyRandomValuesStorage) -> int:
    return storage.count(RandomValuesFilter(experiment_name=experiment))


if __name__ == "__main__":
    connection = "sqlite:///samples.db"
    open_storage(connection)  # Подготовить таблицы до запуска исполнителей.
    with Scheduler(4, partial(open_storage, connection)) as scheduler:
        counts = scheduler.run(
            partial(count_samples, name) for name in ("experiment-a", "experiment-b")
        )
```

Шаги вычислений передают `SampleSource` как контекст: загрузка каждой следующей
порции данных использует тот же источник. Генерация использует `no_context`.
`GenerationTaskSpec.generator` содержит настроенный экземпляр
`AbstractRVSGenerator`; процесс получает его сериализованную копию с каждым
заданием. Генератор должен поддерживать pickle. Его конструктор не вызывается
повторно по сохранённым параметрам. Фактические параметры записываемых выборок
берутся из генератора перед генерацией. Стабильный код серии передаётся отдельно
через `GenerationData.generator_code` и `GenerationTaskSpec.generator_code`.
Сохранение результатов шагов через `BufferedSaver` выполняется в основном
процессе. Пользовательские задания могут самостоятельно читать и записывать
данные через свой контекст.

Размер пакета записи вычислений задаётся через `execute.write_batch_size`
(положительное целое, по умолчанию `20`). Фабрики передают настройку в
`ParallelExecutionStep`; для time complexity она проходит через
`TimeComplexityExecutionContext` и передаётся также в `bulk_insert`.
Лимит измеряется в результатах задач: каждый результат может содержать массив
из многих повторений. Полные пакеты сохраняются по мере поступления результатов,
остаток — при завершении или ошибке вычислений. `_collect_tasks` допускает
`Iterable`, поэтому базовому шагу не требуется заранее знать число задач.
