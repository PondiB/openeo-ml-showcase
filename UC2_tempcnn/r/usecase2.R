library(openeo)

require_env <- function(name) {
  value <- Sys.getenv(name, unset = "")
  if (!nzchar(value)) {
    stop(sprintf("Missing required environment variable: %s", name), call. = FALSE)
  }
  value
}

normalize_host <- function(raw_host) {
  if (grepl("^https?://", raw_host)) {
    raw_host
  } else {
    paste0("http://", raw_host)
  }
}

host <- normalize_host(require_env("OPENEO_HOST"))
user <- require_env("OPENEO_USER")
password <- require_env("OPENEO_PASSWORD")
output_dir <- Sys.getenv("OUTPUT_DIR", unset = "/work/results")
dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)

message(sprintf("Connecting to openEO backend at: %s", host))
connect_with_retry <- function(host, user, password, attempts = 12, sleep_seconds = 5) {
  last_error <- NULL
  for (i in seq_len(attempts)) {
    attempt_msg <- sprintf("Connection attempt %d/%d", i, attempts)
    message(attempt_msg)
    trial <- try({
      con <- connect(host = host)
      login(con = con, user = user, password = password)
    }, silent = TRUE)
    if (!inherits(trial, "try-error")) {
      return(trial)
    }
    last_error <- trial
    if (i < attempts) {
      Sys.sleep(sleep_seconds)
    }
  }
  stop(
    sprintf(
      "Failed to connect/login to backend '%s' after %d attempts. Last error: %s",
      host, attempts, as.character(last_error)
    ),
    call. = FALSE
  )
}

connection <- connect_with_retry(host = host, user = user, password = password)
p <- processes(con = connection)

spatial_extent <- list(west = -63.9, east = -62.9, south = -9.14, north = -8.14)

temporal_extent <- c("2022-01-01", "2022-12-31")

cube_period <- Sys.getenv("UC2_REGULARIZE_PERIOD", unset = "P16D")
if (!nzchar(cube_period)) cube_period <- "P16D"

res_raw <- Sys.getenv("UC2_GRID_RESOLUTION", unset = "30")
resolution <- suppressWarnings(as.numeric(res_raw))
if (!is.finite(resolution) || resolution <= 0) {
  resolution <- 30
}

message(sprintf(
  "Inference cube: temporal %s … %s, regularize period %s, resolution %gm",
  temporal_extent[[1]],
  temporal_extent[[2]],
  cube_period,
  resolution
))

tempcnn_model_init <- p$mlm_class_tempcnn(
  optimizer = "adam",
  learning_rate = 0.0005,
  seed = 42
)

deforestation_data <- "https://github.com/e-sensing/sitsdata/raw/main/data/samples_deforestation_rondonia.rds"

tempcnn_model <- p$ml_fit(
  model = tempcnn_model_init,
  training_set = deforestation_data,
  target = "label"
)

band_spec <- trimws(Sys.getenv("UC2_COLLECTION_BANDS", unset = ""))
load_args <- list(
  id = "mpc-sentinel-2-l2a",
  spatial_extent = spatial_extent,
  temporal_extent = temporal_extent
)
if (nzchar(band_spec)) {
  band_list <- trimws(strsplit(band_spec, ",", fixed = TRUE)[[1]])
  band_list <- band_list[nzchar(band_list)]
  if (length(band_list)) {
    load_args$bands <- band_list
    message(sprintf("load_collection bands override: %s", paste(band_list, collapse = ", ")))
  }
}
if (is.null(load_args$bands)) {
  message("load_collection bands: all available collection bands (including SCL).")
}
datacube <- do.call(p$load_collection, load_args)

datacube <- p$cube_regularize(
  data = datacube,
  period = cube_period,
  resolution = resolution
)

datacube <- p$ndvi(
  data = datacube,
  red = "B04",
  nir = "B08",
  target_band = "NDVI"
)

prediction <- p$ml_predict(data = datacube, model = tempcnn_model)
ml_job <- p$save_result(data = prediction, format = "GTiff")

job <- create_job(
  graph = ml_job,
  title = "Use Case 2: TempCNN Train + Inference",
  con = connection
)
job <- start_job(job, con = connection)

message("Submitted job successfully:")
print(job)

poll_seconds <- as.numeric(Sys.getenv("JOB_POLL_SECONDS", unset = "15"))
max_wait_seconds <- as.numeric(Sys.getenv("JOB_MAX_WAIT_SECONDS", unset = "86400"))
if (!is.finite(poll_seconds) || poll_seconds < 1) {
  poll_seconds <- 15
}
if (!is.finite(max_wait_seconds) || max_wait_seconds < poll_seconds) {
  max_wait_seconds <- 86400
}

wait_until_job_terminal <- function(job, con, poll_sec, max_sec) {
  start <- Sys.time()
  repeat {
    info <- describe_job(job, con = con)
    status_raw <- info$status
    status <- if (is.null(status_raw)) "" else tolower(as.character(status_raw))
    elapsed <- as.numeric(difftime(Sys.time(), start, units = "secs"))
    message(sprintf("[%.0fs] Job status: %s", elapsed, status_raw))

    if (status %in% c("finished", "completed", "done")) {
      return(info)
    }
    if (status %in% c("error", "failed")) {
      stop(sprintf("Job failed with status: %s", status_raw), call. = FALSE)
    }
    if (status %in% c("canceled", "cancelled")) {
      stop(sprintf("Job was canceled: %s", status_raw), call. = FALSE)
    }

    if (elapsed > max_sec) {
      stop(
        sprintf(
          "Timed out after %.0fs waiting for job (max JOB_MAX_WAIT_SECONDS=%s)",
          elapsed,
          max_sec
        ),
        call. = FALSE
      )
    }
    Sys.sleep(poll_sec)
  }
}

wait_until_job_terminal(
  job = job,
  con = connection,
  poll_sec = poll_seconds,
  max_sec = max_wait_seconds
)

message(sprintf("Job finished. Downloading results to %s", output_dir))
download_results(job = job, folder = output_dir, con = connection)
message("Done.")
