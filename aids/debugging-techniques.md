# Debugging techniques

Three techniques for bug-shaped tasks. The standing rule above all of them: **understand the root cause before proposing any fix** — never patch the symptom.

> Adapted from superpowers (`systematic-debugging/`: root-cause-tracing, defense-in-depth, condition-based-waiting; MIT, Jesse Vincent).

## The process (before reaching for a technique)

The techniques below only pay off inside a discipline:

1. **Reproduce consistently first** — an intermittent repro is itself the first bug to fix; you cannot confirm a fix you cannot trigger.
2. **One written hypothesis at a time**, tested with the smallest change that would confirm or kill it.
3. **A failing test before the fix** — capture the bug as a test that fails first, so the fix has a witness and the bug can't silently return.
4. **Fix at the root, not the symptom** (technique 1).
5. **After three failed fixes, stop.** This is not a failed hypothesis, it's a wrong model — escalate to the human (core.md's ask-the-human gate). Do not keep patching.

## 1. Root-cause tracing

Bugs often manifest deep in the call stack (file created in the wrong place, database opened with the wrong path). Fixing where the error appears treats a symptom. Instead trace backward: symptom → the code that directly caused it → what called that → what value was passed → where that value originated. Fix at the source.

When you can't trace by reading, instrument: log directory/cwd/env plus `new Error().stack` **before** the dangerous operation (in tests use `console.error` — loggers may be suppressed), run, and read the captured chains.

When something pollutes the workspace during tests and you don't know which test: bisect — run the suite file-by-file, checking for the artifact after each, and stop at the first polluter:

```bash
shopt -s globstar            # without this, ** matches only one directory level
for t in src/**/*.test.ts; do
  npx vitest run "$t" >/dev/null 2>&1
  [ -e .git-pollution-marker ] && { echo "POLLUTER: $t"; break; }
done
```

## 2. Defense in depth

After finding the root cause, one validation feels sufficient — but other code paths, refactors, and mocks bypass single checks. Make the bug **structurally impossible** by validating at every layer the data passes through:

1. **Entry point** — reject obviously invalid input at the API boundary (empty/nonexistent/wrong type);
2. **Business logic** — assert the data makes sense for this operation;
3. **Environment guards** — refuse dangerous operations in the wrong context (e.g. in tests, refuse `git init` outside the temp dir);
4. **Debug instrumentation** — log context + stack before the dangerous operation, for forensics when the other layers fail.

Then test the layers: try to bypass layer 1 and verify layer 2 catches it. Each layer catches cases the others miss.

## 3. Condition-based waiting (flaky tests)

Tests that guess at timing (`sleep`, arbitrary `setTimeout`) pass on fast machines and fail under load. **Wait for the condition you actually care about, not a guess about how long it takes:**

```typescript
// ❌ await new Promise(r => setTimeout(r, 50));
// ✅ await waitFor(() => getResult() !== undefined, 'result ready');

async function waitFor<T>(cond: () => T | undefined | null | false,
                          desc: string, timeoutMs = 5000): Promise<T> {
  const start = Date.now();
  while (true) {
    const r = cond();
    if (r) return r;
    if (Date.now() - start > timeoutMs)
      throw new Error(`Timeout waiting for ${desc} after ${timeoutMs}ms`);
    await new Promise(r => setTimeout(r, 10));
  }
}
```

Mistakes to avoid: polling every 1 ms (wasteful); no timeout (hangs forever); caching state outside the loop (stale reads). An arbitrary delay is only acceptable when testing *actual timing behavior* (debounce/throttle) — and then it must follow a condition-wait, be derived from known timing, and carry a comment saying why.
