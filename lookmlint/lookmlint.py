# pylint: disable=invalid-name,missing-docstring
from collections import Counter
import os

import yaml

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


def duplicated_view_labels(explore):
    c = Counter(v.display_label() for v in explore.views)
    return {label: n for label, n in c.items() if n > 1}


def label_issues(label, acronyms=None, abbreviations=None):
    acronyms = [] if acronyms is None else acronyms
    abbreviations = [] if abbreviations is None else abbreviations
    def _contains_bad_acronym_usage(label, acronym):
        words = label.split(' ')
        # drop plural 's' from words
        if not acronym.lower().endswith('s'):
            words = [w if not w.endswith('s') else w[:-1] for w in words]
        return any(acronym.upper() == w.upper() and w == w.title() for w in words)

    def _contains_bad_abbreviation_usage(label, abbreviation):
        return any(abbreviation.lower() == k.lower() for k in label.split(' '))

    acronyms_used = [
        a.upper() for a in acronyms if _contains_bad_acronym_usage(label, a)
    ]
    abbreviations_used = [
        a.title() for a in abbreviations if _contains_bad_abbreviation_usage(label, a)
    ]
    return acronyms_used + abbreviations_used


def view_label_issues(explore, acronyms=None, abbreviations=None):
    acronyms = [] if acronyms is None else acronyms
    abbreviations = [] if abbreviations is None else abbreviations
    results = {}
    for v in explore.views:
        issues = label_issues(v.display_label(), acronyms, abbreviations)
        if issues == []:
            continue
        results[v.display_label()] = issues
    return results


def explore_label_issues(model, acronyms=None, abbreviations=None):
    acronyms = [] if acronyms is None else acronyms
    abbreviations = [] if abbreviations is None else abbreviations
    results = {}
    for e in model.explores:
        issues = label_issues(e.display_label(), acronyms, abbreviations)
        if issues == []:
            continue
        results[e.display_label()] = issues
    return results


def mismatched_view_name(view):
    if view.name == view.filename[: -len('.view.lkml')]:
        return False
    return True


def field_label_issues(view, acronyms=None, abbreviations=None):
    acronyms = [] if acronyms is None else acronyms
    abbreviations = [] if abbreviations is None else abbreviations
    results = {}
    for f in view.fields:
        if f.is_hidden:
            continue
        issues = label_issues(f.display_label(), acronyms, abbreviations)
        if issues == []:
            continue
        results[f.display_label()] = issues
    return results


def missing_timeframes(field, timeframes=None):
    timeframes = set() if timeframes is None else set(timeframes)
    field_timeframes = set()

    if field.is_hidden:
        return {}

    if hasattr(field, 'timeframes') and field.timeframes is not None:
        field_timeframes = set(field.timeframes)

    missing_timeframes = list(timeframes.difference(field_timeframes))

    return {'Missing Timeframe(s):': missing_timeframes} if missing_timeframes else {}


def field_missing_timeframes(view, timeframes=None):
    timeframes = [] if timeframes is None else timeframes
    results = {}
    for f in view.fields:
        if f.type not in ('date', 'date_time', 'time'):
            continue
        issues = missing_timeframes(f, timeframes)
        if not issues:
            continue
        results[f.display_label()] = issues
    return results


def derived_table_contains_semicolon(view):
    return view.derived_table_sql is not None and ';' in view.derived_table_sql


def unused_includes(model):
    # if all views in a project are imported into a model,
    # don't suggest any includes are unused
    if model.included_views == ['*']:
        return []
    explore_view_sources = [v.source_view.name for v in model.explore_views()]
    return sorted(list(set(model.included_views) - set(explore_view_sources)))


def _parse_checks(checks):
    for c in checks:
        if c not in CHECK_OPTIONS:
            raise Exception('Check: {} (specified in .lintconfig.yml) is not recognised'.format(c))
    if 'all' in checks:
        checks = list(set(CHECK_OPTIONS) - set(['all']))
    return sorted(checks)


def read_lint_config(repo_path):
    # read .lintconfig.yml
    full_path = os.path.expanduser(repo_path)
    config_filepath = os.path.join(full_path, '.lintconfig.yml')
    acronyms = []
    abbreviations = []
    timeframes = []
    checks = []
    if os.path.isfile(config_filepath):
        with open(config_filepath) as f:
            config = yaml.full_load(f)
            acronyms = config.get('acronyms', acronyms)
            abbreviations = config.get('abbreviations', abbreviations)
            timeframes = config.get('timeframes', timeframes)
            checks = config.get('checks', checks)

    checks = _parse_checks(checks)
    return {'acronyms': acronyms, 'abbreviations': abbreviations, 'timeframes': timeframes, 'checks': checks}


def lint_missing_timeframes(lkml, timeframes):
    if not timeframes:
        return {}

    # check for missing timeframe issues
    issues_field_dates = {}
    for v in lkml.views:
        issues = field_missing_timeframes(v, timeframes)
        if issues != {}:
            issues_field_dates[v.name] = issues
    return issues_field_dates


def lint_labels(lkml, acronyms, abbreviations):

    # check for acronym and abbreviation issues
    issues_explore_labels = {}
    for m in lkml.models:
        issues = explore_label_issues(m, acronyms, abbreviations)
        if issues != {}:
            issues_explore_labels[m.name] = issues
    issues_explore_view_labels = {}
    for m in lkml.models:
        for e in m.explores:
            issues = view_label_issues(e, acronyms, abbreviations)
            if issues != {}:
                if m.name not in issues_explore_view_labels:
                    issues_explore_view_labels[m.name] = {}
                issues_explore_view_labels[m.name][e.name] = issues
    issues_field_labels = {}
    for v in lkml.views:
        issues = field_label_issues(v, acronyms, abbreviations)
        if issues != {}:
            issues_field_labels[v.name] = issues

    # create overall labels issues dict
    all_label_issues = {}
    if issues_explore_labels != {}:
        all_label_issues['explores'] = issues_explore_labels
    if issues_explore_view_labels != {}:
        all_label_issues['explore_views'] = issues_explore_view_labels
    if issues_field_labels != {}:
        all_label_issues['fields'] = issues_field_labels
    return all_label_issues


def lint_duplicate_view_labels(lkml):
    issues = {}
    for m in lkml.models:
        for e in m.explores:
            dupes = duplicated_view_labels(e)
            if dupes == {}:
                continue
            if m.name not in issues:
                issues[m.name] = {}
            if e.name not in issues[m.name]:
                issues[m.name][e.name] = dupes
    return issues


def lint_sql_references(lkml):
    # check for raw SQL field references
    raw_sql_refs = {}
    for m in lkml.models:
        for e in m.explores:
            for v in e.views:
                if not v.contains_raw_sql_ref():
                    continue
                if m.name not in raw_sql_refs:
                    raw_sql_refs[m.name] = {}
                if e.name not in raw_sql_refs[m.name]:
                    raw_sql_refs[m.name][e.name] = {}
                raw_sql_refs[m.name][e.name][v.name] = v.sql_on
    return raw_sql_refs


def lint_view_primary_keys(lkml):
    # check for missing primary keys
    return [v.name for v in lkml.views if not v.primary_key()]


def lint_unused_includes(lkml):
    # check for unused includes
    return {
        m.name: unused_includes(m) for m in lkml.models if unused_includes(m) != []
    }


def lint_unused_view_files(lkml):
    # check for unused view files
    return lkml.unused_view_files()


def lint_missing_view_sql_definitions(lkml):
    return [
        v.name
        for v in lkml.views
        if not v.sql_definition()
           and v.extends == []
           and any(f.sql and '${TABLE}' in f.sql for f in v.fields)
    ]


def lint_semicolons_in_derived_table_sql(lkml):
    return [v.name for v in lkml.views if derived_table_contains_semicolon(v)]


def lint_mismatched_view_names(lkml):
    return {v.filename: v.name for v in lkml.views if mismatched_view_name(v)}


def _run_check(check_name, lkml, lint_config):
    if check_name == 'label-issues':
        return lint_labels(
            lkml=lkml,
            acronyms=lint_config['acronyms'],
            abbreviations=lint_config['abbreviations'],
        )
    if check_name == 'missing-timeframes':
        return lint_missing_timeframes(
            lkml=lkml,
            timeframes=lint_config['timeframes'],
        )
    if check_name == 'raw-sql-in-joins':
        return lint_sql_references(lkml)
    if check_name == 'unused-includes':
        return lint_unused_includes(lkml)
    if check_name == 'unused-view-files':
        return lint_unused_view_files(lkml)
    if check_name == 'views-missing-primary-keys':
        return lint_view_primary_keys(lkml)
    if check_name == 'duplicate-view-labels':
        return lint_duplicate_view_labels(lkml)
    if check_name == 'missing-view-sql-definitions':
        return lint_missing_view_sql_definitions(lkml)
    if check_name == 'semicolons-in-derived-table-sql':
        return lint_semicolons_in_derived_table_sql(lkml)
    if check_name == 'mismatched-view-names':
        return lint_mismatched_view_names(lkml)
    raise Exception(f'Check: {check_name} not recognized')


def run_lint_checks(repo_path, lkml):
    """run the checks as specified in .lintconfig.yml"""

    lint_config = read_lint_config(repo_path)
    checks = lint_config['checks']

    return {
        check_name: _run_check(check_name, lkml, lint_config)
        for check_name in checks
    }
