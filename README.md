# Report for Assignment 1

## Project chosen

Name: discord.py

URL: https://github.com/Rapptz/discord.py

Number of lines of code and the tool used to count it: 68275 using `lizard discord tests setup.py`

Programming language: Python

## Coverage measurement

### Existing tool

The coverage tool [coverage.py](https://coverage.readthedocs.io/en/7.5.3/) was used for this project.
After installing the dependencies and executing `coverage run -m pytest` we get the following output:
![63781](https://github.com/tthijm/sep/assets/74216566/0962f4e0-a7f4-45c0-ab12-59110c55d6c2)

Running `coverage html` and opening the document in the browser gives the following:
![23724](https://github.com/tthijm/sep/assets/74216566/5991a9ef-81a1-494f-8016-700ee72d375e)
![4629](https://github.com/tthijm/sep/assets/74216566/83bdba3d-9217-4be0-a67c-9ae2f0db3ad9)

### Your own coverage tool

<The following is supposed to be repeated for each group member>

<Group member name>

<Function 1 name>

<Show a patch (diff) or a link to a commit made in your forked repository that shows the instrumented code to gather coverage measurements>

<Provide a screenshot of the coverage results output by the instrumentation>

<Function 2 name>

<Provide the same kind of information provided for Function 1>

Thijmen

flatten_literal_params

[commit](https://github.com/tthijm/sep/commit/2afde74ee94eb7e6cdc476356aa41f1ca09d87cf)

![](./assets/flatten_literal_params_custom.png)

\_human_join

[commit](https://github.com/tthijm/sep/commit/88c98ebc05c4d67bcdce7d3046ffa786f79b9284)

![](./assets/_human_join_custom.png)

## Coverage improvement

### Individual tests

<The following is supposed to be repeated for each group member>

<Group member name>

<Test 1>

<Show a patch (diff) or a link to a commit made in your forked repository that shows the new/enhanced test>

<Provide a screenshot of the old coverage results (the same as you already showed above)>

<Provide a screenshot of the new coverage results>

<State the coverage improvement with a number and elaborate on why the coverage is improved>

<Test 2>

<Provide the same kind of information provided for Test 1>

Thijmen

test_flatten_literal_params

[commit](https://github.com/tthijm/sep/commit/18e8104041610c32f9dedff6740688c4d1934550) + [commit](https://github.com/tthijm/sep/commit/138ca9a4c4b0a5f8fba254271f6b913b80d20b95)

![](./assets/flatten_literal_params_before.png)

![](./assets/flatten_literal_params_after.png)

The coverage improvement is +100%.
The coverage has been improved, because `flatten_literal_params` used to not be tested, while the new `test_flatten_literal_params` considers every branch to be taken.

test\_\_human_join

[commit](https://github.com/tthijm/sep/commit/92796db0afb5feff4b51b3c7e4874c2ba0eae7b9)

![](./assets/_human_join_before.png)

![](./assets/_human_join_after.png)

The coverage improvement is +100%.
The coverage has been improved, because `_human_join` used to not be tested, while the new `test__human_join` considers every branch to be taken.

### Overall

<Provide a screenshot of the old coverage results by running an existing tool (the same as you already showed above)>

<Provide a screenshot of the new coverage results by running the existing tool using all test modifications made by the group>

## Statement of individual contributions

<Write what each group member did>
