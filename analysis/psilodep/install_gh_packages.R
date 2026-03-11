# this helper script downloads the dmetar, metapsyData, and metapsyTools libraries using the devtools package. 
library(remotes)

# Check if R package dmetar is installed on the machine.
if ("dmetar" %in% rownames(installed.packages())) {
  cat("dmetar is already installed.\n")
} else {
  # Install dmetar
  remotes::install_github("MathiasHarrer/dmetar")
}

# Check if R package metapsyData is installed on the machine.
if ("metapsyData" %in% rownames(installed.packages())) {
  cat("metapsyData is already installed.\n")
} else {
  # Install metapsyData
  remotes::install_github("metapsy-project/metapsyData")
}

# Check if R package metapsyTools is installed on the machine.
if ("metapsyTools" %in% rownames(installed.packages())) {
  cat("metapsyData is already installed.\n")
} else {
  cat("metapsyData is not installed. Proceeding...\n")
  # Install metapsyTools
  remotes::install_github(
    "metapsy-project/metapsyTools",
    build_vignettes = TRUE)
}
