# Simulation Development Playbook

**Patterns learned during SOCIETAS simulation engine implementation.**

---

## Pattern 7: Engine Integration — start() before tick()

**What happened:** `SimulationEngine.tick()` was a stub while `run_tick()` existed as a
standalone function. The engine needed a `start()` method to initialize agents/RNG before
`tick()` could work. `tick()` raises `RuntimeError` if `start()` wasn't called.

**Rule:** Always check if there's a lifecycle method (start/init/setup) that must be
called before the main operation. Document the call order explicitly. Test the error
case (calling tick() before start() should raise a clear error, not crash silently).

**Code pattern:**
```python
engine = SimulationEngine(config)
engine.start(ai_router=router)  # MUST call before tick()
result = engine.tick()          # RuntimeError if start() not called
```
