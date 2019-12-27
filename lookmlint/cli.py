# pylint: disable=missing-docstring,invalid-name
import json

import click

from . import lookml
from . import lookmlint


CHECK_OPTIONS = [
    'all',
    'label-issues',
    'missing-timeframes',
    'raw-sql-in-joins',
    'unused-includes',
    'unused-view-files',
    'views-missing-primary-keys',
    'duplicate-view-labels',
    'missing-view-sql-definitions',
    'semicolons-in-derived-table-sql',
    'mismatched-view-names',
]


def _parse_checks(checks):
    checks = [c.strip() for c in checks.split(',')]
    for c in checks:
        if c not in CHECK_OPTIONS:
            raise click.BadOptionUsage(f'{c} not in {CHECK_OPTIONS}')
    if 'all' in checks:
        checks = list(set(CHECK_OPTIONS) - set(['all']))
    return sorted(checks)


def _run_check(check_name, lkml, lint_config):
    if check_name == 'label-issues':
        return lookmlint.lint_labels(
            lkml=lkml,
            acronyms=lint_config['acronyms'],
            abbreviations=lint_config['abbreviations'],
        )
    if check_name == 'missing-timeframes':
        return lookmlint.lint_missing_timeframes(
            lkml=lkml,
            timeframes=lint_config['timeframes'],
        )
    if check_name == 'raw-sql-in-joins':
        return lookmlint.lint_sql_references(lkml)
    if check_name == 'unused-includes':
        return lookmlint.lint_unused_includes(lkml)
    if check_name == 'unused-view-files':
        return lookmlint.lint_unused_view_files(lkml)
    if check_name == 'views-missing-primary-keys':
        return lookmlint.lint_view_primary_keys(lkml)
    if check_name == 'duplicate-view-labels':
        return lookmlint.lint_duplicate_view_labels(lkml)
    if check_name == 'missing-view-sql-definitions':
        return lookmlint.lint_missing_view_sql_definitions(lkml)
    if check_name == 'semicolons-in-derived-table-sql':
        return lookmlint.lint_semicolons_in_derived_table_sql(lkml)
    if check_name == 'mismatched-view-names':
        return lookmlint.lint_mismatched_view_names(lkml)
    raise Exception(f'Check: {check_name} not recognized')


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
@click.option(
    '--checks',
    required=False,
    type=click.STRING,
    default='all',
    show_default=True,
    help='\n'.join(CHECK_OPTIONS),
)
@click.option('--json', 'json_output', is_flag=True, help='Format output as json')
def lint(repo_path, checks, json_output):
    checks = _parse_checks(checks)
    lkml = lookml.LookML(repo_path)
    lint_config = lookmlint.read_lint_config(repo_path)
    lint_results = {
        check_name: _run_check(check_name, lkml, lint_config) for check_name in checks
    }
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
