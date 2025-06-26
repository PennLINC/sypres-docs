# this helper script downloads the metapsyData library using the devtools package. 
library(remotes)
library(gitcreds)

# Check if R package metapsyData is installed on the machine. If yes, exit script. If no, proceed
if ("metapsyData" %in% rownames(installed.packages())) {
  cat("metapsyData is already installed. Exiting script.\n")
  quit()
} else {
  cat("metapsyData is not installed. Proceeding...\n")
  
  # # Check if GIT_USER is set on the machine
  # git_pat <- Sys.getenv("GITHUB_PAT")
  # 
  # if (git_pat == "") {
  #   # If GIT_USER is not set, prompt the user for their GH PAT
  #   PAT <- readline(prompt = "Paste your GH PAT and hit return: ")
  #   
  #   # Set GIT_USER and GIT_PASS as environment variables
  #   Sys.setenv(GITHUB_PAT = PAT, GIT_PASS = "x-oauth-basic")
  # }
  gitcreds::gitcreds_set()
  
  # Install metapsyData
  remotes::install_github("metapsy-project/metapsyData")
}
