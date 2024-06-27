# Report for Assignment 1

## Project chosen

Name: **mygpo**

URL: (https://github.com/gpodder/mygpo)

Number of lines of code and the tool used to count it:
**17,266**, counted using **lizard**

Programming language: **Python**

## Coverage measurement

### Existing tool

<Inform the name of the existing tool that was executed and how it was executed>

Since our project was written in python, we used **Coverage.py** to measure the coverage of the tests.

To run the tool, the following steps were taken:

1. Navigate to the cloned **mygpo** directory
2. Run the command: `coverage run --source="*" manage.py test` replacing the `*` with the desired directory (**mygp** if running over the entire project)
3. Run the command `coverage report` to produce a report on the terminal
4. (Optional) Run the command `coverage html` to produce an **html** version of the report

<Show the coverage results provided by the existing tool with a screenshot>

![Initial Coverage Results](coverage/coverage_before.png "Initial Coverage Results")

### Your own coverage tool

<The following is supposed to be repeated for each group member>

#### Hussein Sarrar

<Function 1 name>

##### Function 1: **upload** in **mygpo/api/legacy.py**

<Show a patch(diff) or provide a link to a commit showing the instrumented function>

[Link to commit](https://github.com/gpodder/mygpo/commit/139b0d6521379a7a70e2e83b8d06b106f4c5b096)

**NOTE:** This commit is not the first commit showing the instrumentation, rather a second commit where I expanded coverage to take invisible else clauses into account.


<Provide a screenshot of the coverage results output by the instrumentation>

The function was not being tested initially, and so produced no coverage results.


<Provide the same information for function 2>

###### Function 2: **view_or_basicauth** in **mygpo/userfeeds/auth.py**

[Link to commit](https://github.com/gpodder/mygpo/commit/139b0d6521379a7a70e2e83b8d06b106f4c5b096)

**NOTE:** This commit is not the first commit showing the instrumentation, rather a second commit where I expanded coverage to take invisible else clauses into account.

![View_or_basicauth Coverage Results](coverage/report_images/hussein_v_or_ba_cov_results.png "View_or_basicauth Coverage Results")

## Coverage improvement

All coverage results were written to **txt** files

### Individual tests

<The following is supposed to be repeated for each group member>

<Group member name>

#### Hussein Sarrar

<Test 1>

##### Test for function 1: upload


<Show a patch (diff) or a link to a commit made in your forked repository that shows the new/enhanced test>

[Link to commit showing test](https://github.com/gpodder/mygpo/commit/5a18f0d8c9f5c85d0d519091a200da57b221970d),
Test can be found in **mygpo/api/tests.py** file.

<Provide a screenshot of the old coverage results (the same as you already showed above)>

The function was not being tested at all and had 0% coverage.

<Provide a screenshot of the new coverage results>

![Upload Coverage Results](coverage/report_images/hussein_upload_cov_results.png "Upload Coverage Results")

<State the coverage improvement with a number and elaborate on why the coverage is improved>

After creating a new test for it, the coverage achieved was **100%**. All different logical paths through the function were taken, and the results were asserted.

<Test 2>

##### Test for function 2: view_or_basicauth
<Provide the same kind of information provided for Test 1>

[Link to commit showing test](https://github.com/gpodder/mygpo/commit/603b2ef66aab55ada2b820db571e33ad51acb23b),
Test can be found in **mygpo/userfeeds/tests.py** file.

The function was not being tested at all and had 0% coverage.

![View_or_basicauth Coverage Results](coverage/report_images/hussein_v_or_ba_cov_results.png "View_or_basicauth Coverage Results")

After creating a new test for it, the coverage achieved was **100%**. All different logical paths through the function were taken, and the results were asserted.


### Overall

#### Initial coverage

![Initial Coverage Results](coverage/coverage_before.png "Initial Coverage Results")


<Provide a screenshot of the new coverage results by running the existing tool using all test modifications made by the group>


#### Coverage after creating new tests

![Latest Coverage Results](coverage/coverage_after.png "Lates Coverage Results")

#### Result

Achieved an increase of **1.8%** in the **total** coverage of the tests on the project.

## Statement of individual contributions

<Write what each group member did>


### Hussein Sarrar
* Forked github repository and handled creating branches
* Instrumented the **upload** and **view_or_basicauth** functions
* Created new test cases for both functions, achieving 100% coverage on both
* Enured all tests function correctly upon merging

### Mohamed Hussain Sharif
* Counted lines of mygpo using **lizard**
* Instrumented the **episode_status_icon** and **EpisodeUpdater.mark_outdated** functions
* Created new test cases for both functions, achieving 100% coverage on both
* Ran **Coverage.py** on repository before and after merging


### Samuel Power
* Aided in choosing the project and ensuring it was up to requirements
* Instrumented the **episode_status_text** and **normalize_feed_url** functions
* Created new test cases for both functions, achieving 100% coverage on both
*

### Andreas Stolle
* Aided in choosing the project and ensuring it was up to requirements
* Instrumented the **get_urls** and **device_icons** functions
* Created new test cases for both functions, achieving 100% coverage on both
*