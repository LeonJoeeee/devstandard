# A self-hosted runner: ephemeral, one job, then gone

Read this when Actions minutes are the constraint and the human has said to stand one up
(`reference/ci-pipelines.md`). Nothing about the merge gates changes — GitHub still triggers the run,
the workflow still defines it, the verdict still lands on the PR — only the compute moves to a
machine you own.

## Ephemeral, not persistent — and this is the whole decision

A runner comes in two operating models, and the difference is not convenience.

A **persistent** runner registers once and takes job after job. Every job inherits the last one's
workspace: the previous checkout, whatever a step installed, whatever it wrote. Verified on this
method's own repo: a marker file written by job A was still there when job B ran on the same runner,
and the probe step that should have caught it reported success — **because a `run:` block's exit
status is its last command's, and the check was not the last command.** A green run on a persistent
runner means the code passed *on that machine's accumulated state*, which is a weaker claim than the
one check 2 makes.

An **ephemeral** runner (`--ephemeral` at registration) takes exactly one job, deregisters itself,
and exits. A fresh one is started per job from the same image, so every run begins from the image
and nothing else. Verified the same way: two consecutive jobs landed on two different containers,
each found the workspace clean, each removed itself from the repo's runner list on completion.

**Ephemeral is the default this method recommends**, because it is what restores the property a
hosted runner has and a persistent one silently loses — a green run means the code passed. The cost
is an image to maintain and a loop to start runners, both below.

## The minimum that works

An image with the runner and the project's toolchain, and an entrypoint that registers ephemeral and
runs. This is what was built and run; adapt the toolchain line.

```dockerfile
FROM ubuntu:24.04
ARG RUNNER_VERSION                              # no leading v — see the build command below
RUN apt-get update && apt-get install -y --no-install-recommends \
      curl ca-certificates git jq libicu74 \    # + the project's toolchain
    && rm -rf /var/lib/apt/lists/*
RUN useradd -m runner
USER runner
WORKDIR /home/runner
RUN curl -fsSL -o r.tgz https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz \
    && tar xzf r.tgz && rm r.tgz
COPY --chown=runner:runner --chmod=755 entrypoint.sh .
ENTRYPOINT ["./entrypoint.sh"]
```

```sh
#!/bin/bash
# entrypoint.sh — one job, then gone
set -euo pipefail
: "${REPO:?}" "${TOKEN:?}"
./config.sh --unattended --ephemeral --url "https://github.com/${REPO}" --token "${TOKEN}" \
  --name "ephemeral-$(hostname)" --labels self-hosted,ephemeral --work _work
exec ./run.sh
```

Building it — the release tag carries a `v` the download URL does not, so strip it:

```sh
docker build --build-arg RUNNER_VERSION="$(gh api repos/actions/runner/releases/latest --jq '.tag_name | ltrimstr("v")')" -t <image> .
```

Starting one — the registration token is short-lived and single-use, minted per runner. `--rm`, because
the loop below starts a container per job and every finished one is otherwise left behind:

```sh
TOKEN=$(gh api -X POST repos/<owner>/<repo>/actions/runners/registration-token --jq .token)
docker run -d --rm -e REPO=<owner>/<repo> -e TOKEN="$TOKEN" <image>
```

The workflow targets it with `runs-on: [self-hosted, ephemeral]`. A job queued with those labels sits
at `queued` until a runner with them registers; it does not fail.

**The loop is the only part this page does not hand you finished**, because it is where the
environment decides: a `while true` that mints a token and starts a container each time the previous
one exits is enough for one repo on one machine; a fleet wants a controller (actions-runner-controller
on Kubernetes is the maintained one). Either way the invariant is the same — one container, one job.

## What a session can check

```sh
gh api repos/<owner>/<repo>/actions/runners --jq '.runners[] | "\(.name) \(.status) busy=\(.busy)"'
```

An ephemeral runner shows up for the seconds it is alive and then is gone — an empty list is the
normal idle state, not a fault. **The signal that something is wrong is time:** a job sitting at
`queued` for minutes while the list stays empty means no runner is being started for it — the loop
is what needs restarting, and that is the human's, like the machine itself. A persistent runner that shows `offline` is what
`reference/ci-cannot-run.md`'s "self-hosted runner offline" row is about: the platform is up, the
run is queued, and the machine is the human's to restart.

## Two things the machine must not have

**Secrets it does not need.** A runner executes whatever the workflow says with whatever the machine
holds — environment, mounted files, reachable services. The image carries the toolchain and nothing
else; anything a job needs arrives through the workflow's own `secrets:` and lives only for that job.
Ephemeral makes this enforceable — there is no next job to leak into — and persistent makes it a
promise.

**A public repo.** On a public repo, a fork's pull request runs on your hardware once its workflow
is allowed to run — automatically for a repeat contributor, and after one click of approval for a
first-timer under GitHub's default policy. That click is the only thing between a stranger's code
and your machine. `reference/ci-pipelines.md` already says never; ephemeral narrows the blast radius
to one job but does not change the answer.

## Tearing down

A runner that was killed is not a runner that was removed. Deregister first — `./config.sh remove
--token $(gh api -X POST repos/<owner>/<repo>/actions/runners/remove-token --jq .token)` — then stop
the container; otherwise the repo's runner list keeps a ghost that shows `offline` forever, which is
exactly the state a later session will misread. Ephemeral runners do this themselves on exit; a
persistent one is yours to do.
