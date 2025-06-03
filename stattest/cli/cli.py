from click import command, echo

@command()
def cli() -> None:
    echo("I'm working!")
