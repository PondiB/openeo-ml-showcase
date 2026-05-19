library(openeo)
library(jsonlite)

env_with_default <- function(name, default) {
  value <- Sys.getenv(name, unset = default)
  if (!nzchar(value)) default else value
}

normalize_host <- function(raw_host) {
  if (grepl("^https?://", raw_host)) {
    raw_host
  } else {
    paste0("http://", raw_host)
  }
}

connect_with_retry <- function(host, user, password, attempts = 12, sleep_seconds = 5) {
  last_error <- NULL
  for (i in seq_len(attempts)) {
    message(sprintf("Connection attempt %d/%d", i, attempts))
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

host <- normalize_host(env_with_default("OPENEO_HOST", "http://localhost:8000"))
user <- env_with_default("OPENEO_USER", "brian")
password <- env_with_default("OPENEO_PASSWORD", "123456")
output_dir <- env_with_default("OUTPUT_DIR", "./results")
process_graph_path <- env_with_default("PROCESS_GRAPH", "full_pg.json")

dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)

if (!file.exists(process_graph_path)) {
  stop(sprintf("Process graph not found: %s", process_graph_path), call. = FALSE)
}

message(sprintf("Connecting to openEO backend at: %s", host))
connection <- connect_with_retry(host = host, user = user, password = password)

message(sprintf("Loading process graph from: %s", process_graph_path))
pg_json <- read_json(process_graph_path, simplifyVector = FALSE)
graph <- parse_graph(pg_json, con = connection)

message("Submitting batch job")
job <- create_job(
  graph = graph,
  title = "UC1 random forest (openEOcubes)",
  con = connection
)
job <- start_job(job, log = TRUE, con = connection)

poll_seconds <- as.numeric(Sys.getenv("JOB_POLL_SECONDS", unset = "15"))
max_wait_seconds <- as.numeric(Sys.getenv("JOB_MAX_WAIT_SECONDS", unset = "86400"))
if (!is.finite(poll_seconds) || poll_seconds < 1) {
  poll_seconds <- 15
}
if (!is.finite(max_wait_seconds) || max_wait_seconds < poll_seconds) {
  max_wait_seconds <- 86400
}

wait_until_job_terminal(
  job = job,
  con = connection,
  poll_sec = poll_seconds,
  max_sec = max_wait_seconds
)

message(sprintf("Job finished. Downloading results to %s", output_dir))
downloaded <- download_results(job = job, folder = output_dir, con = connection)
message("Done.")
print(downloaded)
