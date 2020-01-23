# pylint: disable=missing-docstring,invalid-name
import json

import click

from . import lookml
from . import lookmlint



@click.group('cli')
def cli():
    pass


@click.command('lint')
@click.argument('repo-path')
@click.option('--json', 'json_output', is_flag=True, help='Format output as json')
def lint(repo_path, json_output):
    lkml = lookml.LookML(repo_path)
    lint_results = lookmlint.run_lint_checks(repo_path, lkml)

    if json_output:
        click.echo(json.dumps(lint_results, indent=4))
    else:
        output_lines = []
        for check_name in sorted(lint_results.keys()):
            results = lint_results[check_name]
            if not (results == [] or results == {}):
                output_lines += ['\n', check_name, '-' * len(check_name)]
                output_lines += _format_output(check_name, results)

        if output_lines != []:
            raise click.ClickException('\n' + '\n'.join(output_lines) + '\n')


cli.add_command(lint)


if __name__ == '__main__':
    cli()
