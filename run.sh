#!/usr/bin/env bash
# Entry point: self-updating Gradle build + run, so the tools are
# usable from the command line without invoking Gradle directly.
#
# Steady state (no source changes): git pull, skip the build entirely
# via the mtime guard, run the installed app. On source changes:
# rebuild with tests (a failing build never replaces the working
# install), then run.
#
# Usage: ./run.sh patterns "pt___" | ./run.sh analysis |
#        ./run.sh fetch | ./run.sh deck
set -uo pipefail
cd "$(dirname "$0")"

APP_ID="wordle"   # must match build/install/<name>
APP_BIN="build/install/$APP_ID/bin/$APP_ID"

git pull --ff-only -q 2>/dev/null || echo "$(date -u +%FT%TZ) git pull failed, running existing code"

# Rebuild only when build inputs are newer than the installed app.
needs_build=false
if [ ! -x "$APP_BIN" ]; then
    needs_build=true
else
    while IFS= read -r f; do
        if [ "$f" -nt "$APP_BIN" ]; then needs_build=true; break; fi
    done < <(find src build.gradle.kts settings.gradle.kts gradle.properties gradle/libs.versions.toml -type f 2>/dev/null)
fi
if "$needs_build"; then
    echo "$(date -u +%FT%TZ) sources changed, rebuilding"
    # --no-daemon: no lingering Gradle daemon between runs.
    # test gates the deploy: installDist never runs if tests fail.
    if ! ./gradlew --no-daemon test installDist; then
        echo "$(date -u +%FT%TZ) build failed" >&2
        [ -x "$APP_BIN" ] || exit 1
        echo "$(date -u +%FT%TZ) running previous install" >&2
    fi
fi

exec "$APP_BIN" "$@"
