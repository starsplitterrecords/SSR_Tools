# SSR MODULE POLICY
Version: 1.0  
Status: Authoritative  
Scope: Entire SSR Tools v8 Codebase

This document defines the mandatory architectural, behavioral, and organizational rules governing all modules in the SSR Tools ecosystem. All developers, integrators, interpreters, and automated generation systems must comply with these policies.

---

# 1. Layered Architecture (Hard Boundary Rules)

The system consists of four layers. All imports and behaviors must respect these boundaries exactly.

## 1.1 helpers/
- Purpose: Low-level utilities (path tools, event bus, ffmpeg path setup).
- May import: standard library only.
- May NOT import: core/, data/, gui/.
- May contain: pure helper functions, no business logic, no stateful components (except EventBus subscription lists).

## 1.2 core/
- Purpose: Business logic, pure computation, domain transformations.
- May import: helpers/, core.models.
- May NOT import: data/, gui/.
- May NOT perform I/O of any kind except writing to explicitly passed file paths.
- Must operate on domain models or primitive types.
- Must NOT rely on global mutable state.

## 1.3 data/
- Purpose: Persistence and filesystem interaction.
- May import: helpers/, core.models.
- May NOT import: gui/.
- Must return fully constructed domain models.
- Must NOT include business logic beyond serialization and validation of stored fields.
- Must NOT implicitly scan folders unless called explicitly.

## 1.4 gui/
- Purpose: UI presentation and interaction only (Tkinter).
- May import: helpers/, core/, data/.
- Must NOT contain any domain logic beyond control flow.
- Must NOT read or write files except through data layer or user file dialogs.
- Must use EventBus for all cross-component signaling.
- Each tab module must be self-contained.

---

# 2. Domain Model Standards

## 2.1 Canonical Models
All modules must use:
- `Work`
- `Alias`
- `SourceFile`
- `Collateral`

## 2.2 Extensions
- Custom or optional metadata must be stored in `.extra`.
- Schema changes require explicit approval; no silent additions.

## 2.3 Serialization
- Models must serialize through `.to_dict()` / `.from_dict()`.
- Data layer must be the only place reading/writing YAML or SQLite.

---

# 3. EventBus Communication Rules

## 3.1 Required Events
All modules modifying persistent data must publish:

```
work_created
work_updated
work_selected
alias_created
alias_updated
```

## 3.2 Custom Events
Allowed only if namespaced:
```
<domain>_<action>
```

Examples:
```
image_generated
scheduler_recalculated
router_imported
```

## 3.3 Subscription Rules
- Tabs must subscribe in their constructor.
- No dynamic subscription outside initialization.
- No direct cross-tab calls; must use EventBus.

---

# 4. GUI Module Standards

## 4.1 Tab Modules
A valid tab must:
- Inherit `tk.Frame`.
- Accept `(parent, eventbus)` in its constructor.
- Implement `refresh()` if it displays dynamic content.
- Use deterministic widget layout.
- Store data in local attributes (e.g., `self._works`).

## 4.2 Dialog Modules
A dialog must:
- Inherit `tk.Toplevel`.
- Use `.transient(parent)` and `.grab_set()`.
- Publish events on completion (e.g., `work_created`).
- Avoid embedding business logic; call core/data functions instead.

## 4.3 UI Behavior Restrictions
- No hidden threads.
- No async.
- Background timers allowed only for router auto-refresh, matching the existing pattern.

---

# 5. Core Engine Standards

## 5.1 Behavior
- Must provide deterministic, stateless functions.
- Must not import Tkinter or data layer.
- May write files only to explicit paths created by the caller.
- Must not discover paths; always receive paths as parameters.

## 5.2 Function Pattern

```python
def action(model: Work | Alias | dict, *, options: dict) -> ResultType:
    ...
```

- Use keyword-only options.
- Never read global configuration directly; caller must supply needed values.

---

# 6. Data Layer Standards

## 6.1 Save Pattern
All write operations involving `Work` must follow:

```
work_repo.save_work(work)
catalog_repo.save_work_to_catalog(work)
```

## 6.2 File and Database Behavior
- Must be explicit, not implicit.
- Must validate expected fields.
- Must not introduce state outside the DB/YAML being modified.

---

# 7. Naming Standards

## 7.1 File Naming
```
gui/tabs/<feature>_tab.py
gui/dialogs/<feature>_dialog.py
core/<domain>/<engine>.py
data/<entity>_repo.py
helpers/<utility>.py
```

## 7.2 Class Naming
```
<Feature>Tab
<Feature>Dialog
<Domain>Engine
<Entity>Repo
```

## 7.3 Function Naming
Consistent verb-first form:
```
load_*
save_*
generate_*
validate_*
compute_*
extract_*
```

No ambiguous abbreviations.

---

# 8. Module Generation Rules (for automated systems)

## 8.1 Output Requirements
- Entire file must be generated with no ellipses or placeholders.
- Code must be syntactically valid Python.
- Must conform to architecture rules above.

## 8.2 Allowed Behaviors
- Full rewrites of modules.
- Structural improvements if they reduce coupling and follow all policy rules.

## 8.3 Forbidden Behaviors
- Partial rewrites.
- Silent modifications to unrelated modules.
- Introducing compatibility layers for legacy code.
- Introducing unapproved dependencies.

---

# 9. Compliance Checklist

A module is considered valid only if ALL of these conditions are true:

- [ ] Imports respect layer boundaries.  
- [ ] No domain logic inside GUI.  
- [ ] No I/O inside core.  
- [ ] Data layer uses correct save/load patterns.  
- [ ] Tab uses EventBus correctly.  
- [ ] Tab implements `refresh()` if needed.  
- [ ] Naming conventions followed.  
- [ ] No hidden state, threads, or async.  
- [ ] No schema changes outside `.extra`.  
- [ ] Code outputs deterministic behavior.

---

# 10. Enforcement

Any module failing this policy:
- Must be rejected by Integrator Chat.  
- Must be regenerated or refactored before inclusion.  
- Must not be merged into the project.
