## Project Setup

### 1. Clone the repository:
To get started, clone this repository using the following command:

`git clone git@github.com:PennLINC/sypres-docs.git`

### 2. Install R and RStudio:
Ensure that you have R and RStudio installed on your machine.
Current R version: `4.4.1`

### 3. Set up the R Environment:
Open RStudio and start a new Project: `File->New Project->From existing directory` and select the `sypres-docs/analysis` directory.


Once you are in the project dirctory, run the setup script from the console:

`source("setup.R")`

You will be prompted to answer if this is the first time you're running PSYPRES on this machine. If you respond `y`, you will be asked a second question. Select `1` to restore the project from the lockfile.

This will install all the required packages as specified in the renv.lock file.

Example readout is below:

```
> source("setup/setup.R")
Is this your first time setting up PSYPRES? [y/n]: y
Initializing a new 'renv' project...
This project already has a lockfile. What would you like to do?

1: Restore the project from the lockfile.
2: Discard the lockfile and re-initialize the project.
3: Activate the project without snapshotting or installing any packages.
4: Abort project initialization.

Selection: 1
The following package(s) will be updated:

# CRAN -----------------------------------------------------------------------
- bit           [* -> 4.0.5]
- bit64         [* -> 4.0.5]
- cli           [* -> 3.6.3]
- clipr         [* -> 0.8.0]
- cpp11         [* -> 0.5.0]
- crayon        [* -> 1.5.3]
- fansi         [* -> 1.0.6]
- glue          [* -> 1.7.0]
- hms           [* -> 1.1.3]
- lifecycle     [* -> 1.0.4]
- magrittr      [* -> 2.0.3]
- pillar        [* -> 1.9.0]
- pkgconfig     [* -> 2.0.3]
- prettyunits   [* -> 1.2.0]
- progress      [* -> 1.2.3]
- R6            [* -> 2.5.1]
- readr         [* -> 2.1.5]
- renv          [* -> 1.0.7]
- rlang         [* -> 1.1.4]
- tibble        [* -> 3.2.1]
- tidyselect    [* -> 1.2.1]
- tzdb          [* -> 0.4.0]
- utf8          [* -> 1.2.4]
- vctrs         [* -> 0.6.5]
- vroom         [* -> 1.6.5]
- withr         [* -> 3.0.1]

# Installing packages --------------------------------------------------------
- Installing R6 ...                             OK [linked from cache]
- Installing bit ...                            OK [linked from cache]
- Installing bit64 ...                          OK [linked from cache]
- Installing cli ...                            OK [linked from cache]
- Installing clipr ...                          OK [linked from cache]
- Installing cpp11 ...                          OK [linked from cache]
- Installing crayon ...                         OK [linked from cache]
- Installing fansi ...                          OK [linked from cache]
- Installing glue ...                           OK [linked from cache]
- Installing rlang ...                          OK [linked from cache]
- Installing lifecycle ...                      OK [linked from cache]
- Installing pkgconfig ...                      OK [linked from cache]
- Installing vctrs ...                          OK [linked from cache]
- Installing hms ...                            OK [linked from cache]
- Installing magrittr ...                       OK [linked from cache]
- Installing utf8 ...                           OK [linked from cache]
- Installing pillar ...                         OK [linked from cache]
- Installing prettyunits ...                    OK [linked from cache]
- Installing progress ...                       OK [linked from cache]
- Installing tibble ...                         OK [linked from cache]
- Installing withr ...                          OK [linked from cache]
- Installing tidyselect ...                     OK [linked from cache]
- Installing tzdb ...                           OK [linked from cache]
- Installing vroom ...                          OK [linked from cache]
- Installing readr ...                          OK [linked from cache]
- Installing renv ...                           OK [linked from cache]

Restarting R session...

- Project '~/Documents/GIT/psypres' loaded. [renv 1.0.7]
```

### 4. Downloading dmetar and metapsy packages
Run the `dmetar_setup.R` script. Select option 3. If using metapsyData or metapsyTools package for, run the `metapsyData_setup.R` and/or `metapsyTools_setup.R` script and also select option 3.

### 5. Updating the renv lockfile

When installing new packages for the repo do so using `renv::install('package_name')` followed by `renv::snapshot()` to install the package into the renv environment and record it in the lockfile. The lockfile will be tracked by git and each time you come back to the repo after pulling changes you should run `renv::restore()` in the console to update your renv library (or, alternatively, rerun `source("setup.R")` and follow the prompts).

Why isn’t my package being snapshot into the lockfile?

For a package to be recorded in the lockfile, it must be both:

Installed your project library, and

Used by the project, as determined by renv::dependencies().

This ensures that only the packages you truly require for your project will enter the lockfile; development dependencies (e.g. devtools) normally should not.


### 6. Using conda for the python env
Collaborators can set up the exact conda environment by running: `conda env create -f environment.yml`

If you update the environment with new packages, you can re-export the environment file: `conda env export > environment.yml`

Commit and push the updated file to keep everyone in sync.
