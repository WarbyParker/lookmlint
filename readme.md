# lookmlint

Lint your LookML.

Provides additional linting checks beyond what is built into the LookML Validator.


## usage

From the CLI:

```
$ lookmlint lint ~/my-lookml-repo
```

Alternatively, specify which `checks` to run:

```
$ lookmlint lint ~/my-lookml-repo --checks label-issues,views-missing-primary-keys
```

For structured output, set the `--json` flag:

```
$ lookmlint lint ~/my-lookml-repo --json
```

### configuration

`lookmlint` looks for a file named `.lintconfig.yml` in your lookML project repo.

Its contents can contain lists of abbreviations and/or acronyms you'd like to flag. More detail below.

#### sample .lintconfig.yml

```yml
abbreviations:
  - num
  - qty
acronyms:
  - aov
  - sms
  - sku
  - sla
timeframes:
  - date
  - month
  - month_name
  - time
  - year
```

## installation

Requires `python3`.

```
$ pip install lookmlint
```

## checks

### `label-issues`

#### acronyms

LookML automatically converts snake case strings (e.g. `unit_cost_usd`) to title case (e.g. `Unit Cost Usd`), which looks funny when using acronyms. Leverages the list of acronyms defined in `.lintconfig.yml`.

**Bad**

```
dimension: unit_cost_usd {
    ...
}
```

**Good**

```
dimension: unit_cost_usd {
    label: "Unit Cost (USD)"
    ...
}
```

#### abbreviations

If you'd prefer some words fully spelled out (e.g. 'Quantity' instead of 'Qty'), define a list of abbreviations for `lookmlint` to catch.


### `raw-sql-in-joins`

Joins should refer to LookML dimensions as opposed to the underlying fields where possible.

For example:

**Bad**

```
join: order_items {
  sql_on: orders.id = order_items.order_id ;;
}
```

**Good**

```
join: order_items {
  sql_on: ${orders.id} = ${order_items.order_id} ;;
}
```

### `missing-timeframes`

Find all date/datetime/time dimensions or dimension groups that are missing any of the timeframes defined in `.lintconfig.yml`.


### `unused-includes`

If your LookML model explicitly specifies views to include, `lookmlint` can catch views that are `include`d in your model but not referenced in any of the explorations in that model.

### `unused-view-files`

Find all view files that aren't referenced in any explorations in your project.

### `views-missing-primary-keys`

Find all view files that don't contain a `primary_key` dimension.

### `duplicate-view-labels`

Find any cases when two `join`s in an exploration end up with the same label.

One way this can unwittingly creep into code is if a `label` is defined in a view file, that view is joined twice to the same exploration, but `view_label`s are not assigned to those joins.

### `missing-view-sql-definitions`

Find any views that do not have a `sql_table_name` or `derived_table` value set.

### `semicolons-in-derived-table-sql`

Find any derived table SQL expressions that contain a rogue semicolon, which will throw errors at query time.

### `mismatched-view-names`

Find any views where the view name does not match the view filename.

## examples

The sample repo at `examples/sample_repo/` contains instances of all linting violations:


```
~/src/lookmlint $$$ lookmlint lint examples/sample_repo/
Error:


duplicate-view-labels
---------------------
Model: test
  Explore: inventory_transfers
    Inventory Locations: 2


label-issues
------------
Fields:
  View: order_items
    - Qty: ['Qty']
    - Unit Cost Usd: ['USD']


missing-timeframes
-----------
View: items
  Field: Created
   - Missing Timeframe(s): ['month_name', 'time']
View: orders
  Field: Placed
   - Missing Timeframe(s): ['date', 'month', 'month_name', 'time', 'year']


mismatched-view-names
---------------------
- items.view.lkml: order_items


missing-view-sql-definitions
----------------------------
- order_items


raw-sql-in-joins
----------------
Model: test
  Explore: orders
    order_items: orders.id = order_items.order_id


semicolons-in-derived-table-sql
-------------------------------
- products


unused-includes
---------------
Model: test
  - web_sessions


unused-view-files
-----------------
- legacy_products
- web_sessions


views-missing-primary-keys
--------------------------
- order_items
```

## adding to CircleCI

We use CircleCI at Warby Parker to run our checks.

Adding the following contents to `.circleci/config.yml` in your LookML project should work for running linting as part of your CI/CD workflow. This all runs in a few seconds, but leveraging caching could also help to speed things up.

Customize the list of checks you run to suit your team's needs, or leave out the `--checks` flag to run all possible lint checks.

```
version: 2
jobs:
  build:
    docker:
      - image: circleci/python:3.6.2-stretch
    working_directory: ~/repo
    steps:
      - checkout
      - run:
          name: Install lookmlint
          command: |
            sudo pip install lookmlint
      - run:
          name: Lint lookml
          command: |
            lookmlint lint . --checks label-issues,unused-includes,unused-view-files,mismatched-view-names,semicolons-in-derived-table-sql,missing-view-sql-definitions
```


## issues?

This repo is still in alpha, so use at your own risk!

Please open an issue for any feature suggestions or bugs, or feel free to open a PR with a fix / feature!
