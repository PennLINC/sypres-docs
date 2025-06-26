# setup.R

# Ensure the script is run in the project directory
if (basename(getwd()) != "analysis") {
  stop("Please run this script from the analysis directory. Start a New Project using the sypres-docs/analysis directory if you have not done so already. See README for instructions.")
}

# Check if 'renv' is installed
if (!requireNamespace("renv", quietly = TRUE)) {
  install.packages("renv")
}

# renv::restore()

# Prompt the user for input
is_first_time <- readline(prompt = "Is this your first time setting up SYPRES on this machine? [y/n]: ")

# Process the user input
if (tolower(is_first_time) %in% c("y", "yes")) {
  cat("Initializing a new 'renv' project...\n")
  renv::init()
} else if (tolower(is_first_time) %in% c("n", "no")) {
  cat("Restoring the project environment from 'renv.lock'...\n")
  renv::restore()
} else {
  cat("Invalid input. Please enter 'y' or 'n'.\n")
  # Optionally, you can re-prompt the user or handle the error as needed
}

renv::status()

cat("Setup complete. You are now ready to start working on the project.\n")

rm(is_first_time)
