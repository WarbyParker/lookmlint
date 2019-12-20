# pylint: disable=invalid-name,missing-docstring,too-few-public-methods,too-many-instance-attributes
import os

import attr
import lkml


@attr.s
class Dimension:

    data = attr.ib(repr=False)
    name = attr.ib(init=False, repr=True)
    type = attr.ib(init=False)
    label = attr.ib(init=False)
    description = attr.ib(init=False, repr=False)
    sql = attr.ib(init=False, repr=False)
    is_primary_key = attr.ib(init=False)
    is_hidden = attr.ib(init=False, repr=False)

    def __attrs_post_init__(self):
        self.name = self.data['name']
        self.type = self.data.get('type', 'string')
        self.label = self.data.get('label')
        self.description = self.data.get('description')
        self.sql = self.data.get('sql')
        self.is_primary_key = self.data.get('primary_key') == 'yes'
        self.is_hidden = self.data.get('hidden') == 'yes'

    def display_label(self):
        return self.label if self.label else self.name.replace('_', ' ').title()


@attr.s
class DimensionGroup:

    data = attr.ib(repr=False)
    name = attr.ib(init=False, repr=True)
    type = attr.ib(init=False)
    label = attr.ib(init=False)
    description = attr.ib(init=False, repr=False)
    timeframes = attr.ib(init=False, repr=False)
    sql = attr.ib(init=False, repr=False)
    is_hidden = attr.ib(init=False, repr=False)

    def __attrs_post_init__(self):
        self.name = self.data['name']
        self.type = self.data.get('type', 'string')
        self.label = self.data.get('label')
        self.description = self.data.get('description')
        self.sql = self.data.get('sql')
        self.timeframes = self.data.get('timeframes')
        self.is_hidden = self.data.get('hidden') == 'yes'

    def display_label(self):
        return self.label if self.label else self.name.replace('_', ' ').title()


@attr.s
class Measure:

    data = attr.ib(repr=False)
    name = attr.ib(init=False, repr=True)
    type = attr.ib(init=False)
    label = attr.ib(init=False)
    description = attr.ib(init=False, repr=False)
    sql = attr.ib(init=False, repr=False)
    is_hidden = attr.ib(init=False, repr=False)

    def __attrs_post_init__(self):
        self.name = self.data['name']
        self.type = self.data.get('type')
        self.label = self.data.get('label')
        self.description = self.data.get('description')
        self.sql = self.data.get('sql')
        self.is_hidden = self.data.get('hidden') == 'yes'

    def display_label(self):
        return self.label if self.label else self.name.replace('_', ' ').title()


@attr.s
class View:

    data = attr.ib(repr=False)
    filename = attr.ib(repr=False)
    name = attr.ib(init=False)
    label = attr.ib(init=False)
    dimensions = attr.ib(init=False, repr=False)
    dimension_groups = attr.ib(init=False, repr=False)
    measures = attr.ib(init=False, repr=False)
    fields = attr.ib(init=False, repr=False)
    extends = attr.ib(init=False, repr=False)
    sql_table_name = attr.ib(init=False, repr=False)
    derived_table_sql = attr.ib(init=False, repr=False)

    def __attrs_post_init__(self):
        self.name = self.data['name']
        self.label = self.data.get('label')
        self.dimensions = [Dimension(d) for d in self.data.get('dimensions', [])]
        self.measures = [Measure(m) for m in self.data.get('measures', [])]
        self.dimension_groups = [
            DimensionGroup(dg) for dg in self.data.get('dimension_groups', [])
        ]
        self.fields = self.dimensions + self.dimension_groups + self.measures
        self.extends = [v.strip('*') for v in self.data.get('extends', [])]
        self.sql_table_name = self.data.get('sql_table_name')
        self.derived_table_sql = None
        if 'derived_table' in self.data:
            self.derived_table_sql = self.data['derived_table']['sql']

    def primary_key(self):
        try:
            return next(d.name for d in self.dimensions if d.is_primary_key)
        except StopIteration:
            return None
        finally:
            pass

    def sql_definition(self):
        priority = [self.sql_table_name, self.derived_table_sql]
        for v in priority:
            if v is not None:
                return v
        return None


@attr.s
class ExploreView:

    data = attr.ib(repr=False)
    explore = attr.ib()
    name = attr.ib(init=False)
    source_view = attr.ib(init=False, repr=False)
    from_view_name = attr.ib(init=False, repr=False)
    view_name = attr.ib(init=False)
    join_name = attr.ib(init=False)
    sql_on = attr.ib(init=False, repr=False)
    view_label = attr.ib(init=False, repr=False)

    def __attrs_post_init__(self):
        self.from_view_name = self.data.get('from')
        self.view_name = self.data.get('view_name')
        self.join_name = self.data.get('name')
        self.sql_on = self.data.get('sql_on')
        self.view_label = self.data.get('view_label')
        name_priority = [self.view_name, self.join_name, self.explore]
        self.name = next(v for v in name_priority if v is not None)

    def source_view_name(self):
        priority = [self.from_view_name, self.view_name, self.join_name, self.explore]
        return next(v for v in priority if v is not None)

    def display_label(self):
        priority = [
            self.view_label,
            self.source_view.label,
            self.name.replace('_', ' ').title(),
        ]
        return next(v for v in priority if v is not None)

    def contains_raw_sql_ref(self):
        if not self.sql_on:
            return False
        raw_sql_words = [
            w
            for line in self.sql_on.split('\n')
            for w in line.split()
            # not a comment line
            if not line.replace(' ', '').startswith('--')
            # doesn't contain lookml syntax
            and not '${' in w and not '}' in w
            # not a custom function with newlined args
            and not w.endswith('(')
            # contains one period
            and w.count('.') == 1
        ]
        return len(raw_sql_words) > 0


@attr.s
class Explore:

    data = attr.ib(repr=False)
    label = attr.ib(init=False)
    model = attr.ib()
    name = attr.ib(init=False)
    views = attr.ib(init=False, repr=False)

    def __attrs_post_init__(self):
        self.name = self.data.get('name')
        self.label = self.data.get('label')
        joined_views = [ExploreView(j, explore=self.name) for j in self.data.get('joins', [])]
        self.views = [ExploreView(self.data, explore=self.name)] + joined_views

    def display_label(self):
        return self.label if self.label else self.name.replace('_', ' ').title()


@attr.s
class Model:

    data = attr.ib(repr=False)
    filename = attr.ib(repr=False)
    explores = attr.ib(init=False, repr=False)
    included_views = attr.ib(init=False, repr=False)
    name = attr.ib(init=False)

    def __attrs_post_init__(self):
        includes = self.data.get('include', [])
        if isinstance(includes, str):
            includes = [includes]
        self.included_views = [i[: -len('.view')] for i in includes]
        self.name = self.filename[: -len('.model.lkml')]
        self.explores = [Explore(e, model=self.name) for e in self.data.get('explores', [])]

    def explore_views(self):
        return [v for e in self.explores for v in e.views]


@attr.s
class LookML:

    lookml_repo_path = attr.ib()
    models = attr.ib(init=False, repr=False)
    views = attr.ib(init=False, repr=False)

    def __attrs_post_init__(self):

        self.models = []
        for model_file in self._model_file_names():
            with open(os.path.join(self.lookml_repo_path, model_file)) as f:
                self.models.append(Model(lkml.load(f), model_file))
        self.views = []
        for view_file in self._view_file_names():
            with open(os.path.join(self.lookml_repo_path, view_file)) as f:
                for view_data in lkml.load(f)['views']:
                    self.views.append(View(view_data, view_file))

        # match explore views with their source views
        for m in self.models:
            for e in m.explores:
                for ev in e.views:
                    source_view = next(
                        v for v in self.views if v.name == ev.source_view_name()
                    )
                    ev.source_view = source_view

    def _view_file_names(self):
        return sorted(
            [f for f in os.listdir(self.lookml_repo_path) if f.endswith('.view.lkml')]
        )

    def _model_file_names(self):
        return sorted(
            [f for f in os.listdir(self.lookml_repo_path) if f.endswith('.model.lkml')]
        )

    def all_explore_views(self):
        explore_views = []
        for m in self.models:
            explore_views += m.explore_views()
        return explore_views

    def unused_view_files(self):
        view_names = [v.name for v in self.views]
        explore_view_names = [v.source_view.name for v in self.all_explore_views()]
        extended_views = [exv for v in self.views for exv in v.extends]
        return sorted(
            list(set(view_names) - set(explore_view_names) - set(extended_views))
        )
