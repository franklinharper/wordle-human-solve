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

# JVM-cluster Gradle home (Frank, 2026-11-17; see TOOLS.md "Gradle
# cluster homes"): in the sandbox, builds run in the JVM cluster's own
# Gradle home, so this repo never contends on another cluster's
# file-access journal, and its builds reuse the cluster's shared
# daemon. Elsewhere (no cluster home present) the default applies.
if [ -d "$HOME/.gradle-jvm" ]; then
    export GRADLE_USER_HOME="$HOME/.gradle-jvm"
    # Pin the build environment inside the sandbox (same
    # derivation as android-build.sh): a Gradle daemon's identity
    # is its JVM + jvmargs, so a caller shell missing JAVA_HOME /
    # JDK_JAVA_OPTIONS forks a second, differently-spec'd daemon
    # on a new random port — a fresh approval card — and on this
    # sandbox (localhost resolves to ::1, daemons bind 127.0.0.1)
    # its handshake fails outright. Deriving the env here makes
    # every invocation present the identical spec, so the cluster
    # daemon starts once and is reused. The proxy credentials
    # rotate per boot: read them fresh from $https_proxy, never
    # persisted.
    if [ -d "$HOME/jdk-21" ]; then
        export JAVA_HOME="$HOME/jdk-21"
        export PATH="$JAVA_HOME/bin:$PATH"
    fi
    export JDK_JAVA_OPTIONS="-Djava.net.preferIPv4Stack=true"
    if [ -n "${https_proxy:-}" ]; then
        # Pure-shell proxy parse (the same splits as the
        # ops.sh scripts): no interpreter in the build path,
        # and no eval of text generated from the
        # credential-bearing URL. The sandbox credential is
        # alphanumeric, so the first-@ / first-: splits are
        # exact for the URL this sandbox issues.
        _rest="${https_proxy#*://}"
        case "$_rest" in
            *@*)
                _auth="${_rest%%@*}"
                _hostport="${_rest##*@}"
                _user="${_auth%%:*}"
                _pass="${_auth#*:}"
                ;;
            *)
                _hostport="$_rest"
                _user=""
                _pass=""
                ;;
        esac
        _host="${_hostport%%:*}"
        _port="${_hostport##*:}"
        JDK_JAVA_OPTIONS="$JDK_JAVA_OPTIONS -Dhttps.proxyHost=$_host -Dhttps.proxyPort=$_port -Dhttp.proxyHost=$_host -Dhttp.proxyPort=$_port"
        if [ -n "$_user" ]; then
            JDK_JAVA_OPTIONS="$JDK_JAVA_OPTIONS -Dhttps.proxyUser=$_user -Dhttps.proxyPassword=$_pass -Dhttp.proxyUser=$_user -Dhttp.proxyPassword=$_pass"
        fi
        unset _rest _auth _hostport _user _pass _host _port
    fi
fi

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
    # Builds run on the JVM cluster's shared daemon (no --no-daemon),
    # serialized per Gradle home by flock: a concurrent build in this
    # home queues here instead of timing out on the journal lock.
    # test gates the deploy: installDist never runs if tests fail.
    GRADLE_CMD=(./gradlew test installDist)
    if command -v flock >/dev/null 2>&1 &&
        [ -n "${GRADLE_USER_HOME:-}" ]; then
        GRADLE_CMD=(flock -w 1800 "$GRADLE_USER_HOME/build.lock"
            ./gradlew test installDist)
    fi
    if ! "${GRADLE_CMD[@]}"; then
        echo "$(date -u +%FT%TZ) build failed" >&2
        [ -x "$APP_BIN" ] || exit 1
        echo "$(date -u +%FT%TZ) running previous install" >&2
    fi
fi

exec "$APP_BIN" "$@"
