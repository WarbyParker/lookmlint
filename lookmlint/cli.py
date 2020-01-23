# pylint: disable=missing-docstring,invalid-name
import json

import click

from . import lookml
from . import lookmlint


def _format_output(check_name, results):
    lines = []
    if check_name == 'label-issues':
        if 'explores' in results:
            lines += ['Explores:']
            for model, model_results in results['explores'].items():
                lines.append(f'  Model: {model}')
                for explore, issues in model_results.items():
                    lines.append(f'    - {explore}: {issues}')
        if 'explore_views' in results:
            lines += ['Explore Views:']
            for model, model_results in results['explore_views'].items():
                lines.append(f'  Model: {model}')
                for explore, joins in model_results.items():
                    lines.append(f'    Explore: {explore}')
                    for join, issues in joins.items():
                        lines.append(f'      - {join}: {issues}')
        if 'fields' in results:
            lines += ['Fields:']
            for view, view_results in results['fields'].items():
                lines.append(f'  View: {view}')
                for field, issues in view_results.items():
                    lines.append(f'    - {field}: {issues}')
    if check_name == 'missing-timeframes':
        for view, view_results in results.items():
            lines.append(f'View: {view}')
            for field, issues in view_results.items():
                lines.append(f'  Field: {field}')
                for issue, timeframe in issues.items():
                    lines.append(f'   - {issue} {timeframe}')
    if check_name == 'raw-sql-in-joins':
        for model, model_results in results.items():
            lines.append(f'Model: {model}')
            for exploration, joins in model_results.items():
                lines.append(f'  Explore: {exploration}')
                for join, sql in joins.items():
                    lines.append(f'    {join}: {sql}')
    if check_name == 'unused-includes':
        for model, includes in results.items():
            lines.append(f'Model: {model}')
            for include in includes:
                lines.append(f'  - {include}')
    if check_name == 'unused-view-files':
        for view in results:
            lines.append(f'- {view}')
    if check_name == 'views-missing-primary-keys':
        for view in results:
            lines.append(f'- {view}')
    if check_name == 'duplicate-view-labels':
        for model, model_results in results.items():
            lines.append(f'Model: {model}')
            for exploration, joins in model_results.items():
                lines.append(f'  Explore: {exploration}')
                for join, num in joins.items():
                    lines.append(f'    {join}: {num}')
    if check_name == 'missing-view-sql-definitions':
        for view in results:
            lines.append(f'- {view}')
    if check_name == 'semicolons-in-derived-table-sql':
        for view in results:
            lines.append(f'- {view}')
    if check_name == 'mismatched-view-names':
        for view_file, view_name in results.items():
            lines.append(f'- {view_file}: {view_name}')
    return lines


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
