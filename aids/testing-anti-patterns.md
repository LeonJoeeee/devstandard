# Testing anti-patterns

Read when writing or changing tests, adding mocks, or tempted to add test-only methods to production code. Core principle: **test what the code does, not what the mocks do.**

> Adapted from superpowers (`test-driven-development/testing-anti-patterns.md`, MIT, Jesse Vincent).

## The iron laws

1. NEVER test mock behavior.
2. NEVER add test-only methods to production classes.
3. NEVER mock without understanding the dependency.

## 1. Testing mock behavior

Asserting that a mock element exists (`getByTestId('sidebar-mock')`) verifies the mock works, not the component. Before asserting on any mock element ask: *am I testing real behavior or mock existence?* If the latter — delete the assertion or unmock the component, and test real behavior (e.g. `getByRole('navigation')`).

## 2. Test-only methods in production

A method only tests call (e.g. `session.destroy()` used solely in `afterEach`) pollutes the production class and is dangerous if ever called for real. Before adding any method ask: *is this only used by tests?* → put it in test utilities instead. *Does this class even own this resource's lifecycle?* → if not, wrong class.

## 3. Mocking without understanding

Mocking a method whose **side effect the test depends on** makes the test pass for the wrong reason or fail mysteriously (e.g. mocking away the call that writes the config a duplicate-detection test needs). Before mocking: list the real method's side effects; check whether the test depends on any; if unsure, **run the test against the real implementation first**, observe what's needed, then mock minimally at the lowest level (the actually-slow/external operation). Red flags: "I'll mock this to be safe", "this might be slow, better mock it".

## 4. Incomplete mocks

A mock response containing only the fields you know about hides structural assumptions — downstream code breaks on the missing ones while tests stay green. Iron rule: **mock the COMPLETE data structure as it exists in reality.** Check the real API response and include all fields the system might consume; if uncertain, include everything documented.

## 5. Tests as afterthought

"Implementation complete, ready for testing" is incomplete work: testing is part of implementation. Write the test, watch it fail against real code, implement to green — the failing-first step is what proves the test tests real behavior rather than its own mocks.

## When mocks get too complex

Warning signs: mock setup longer than the test logic; mocks missing methods the real component has; the test breaks when the mock changes; you can't explain why the mock is needed. Consider an integration test with real components — often simpler than the mock.

## Quick reference

| Anti-pattern | Fix |
|---|---|
| Assert on mock elements | Test the real component or unmock it |
| Test-only methods in production | Move to test utilities |
| Mock without understanding | Understand dependencies first, mock minimally |
| Incomplete mocks | Mirror the real structure completely |
| Tests as afterthought | Failing test first, then implement |
| Over-complex mocks | Switch to integration tests |
