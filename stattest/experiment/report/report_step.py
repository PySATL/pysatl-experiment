def execute_report_step(configuration):
    data_reader = configuration.data_reader
    # Execute before all listeners
    for listener in configuration.listeners:
        listener.before()

    # Process data
    report_builder = configuration.report_builder
    for data in data_reader:
        report_builder.process(data)

    # Build report
    report_builder.build()

    # Execute after all listeners
    for listener in configuration.listeners:
        listener.after()
