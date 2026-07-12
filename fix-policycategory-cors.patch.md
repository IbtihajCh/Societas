# Patch: Fix PolicyCategory Enum Mismatch + CORS Trailing-Slash Redirect

Apply these 4 changes plus delete `societas.db`, then restart both backend and frontend.

---

## 1. `backend/app/repositories/policy_repository.py` — line 110

Replace the `_row_to_policy` method to handle both old int and new string category values:

```python
+_CATEGORY_MAP = ["economic", "social", "environmental", "public_order",
+                 "education", "healthcare", "infrastructure", "cultural"]

 def _row_to_policy(self, row) -> Policy:
     weights_dict = json.loads(row["weights"]) if isinstance(row["weights"], str) else {}
-    raw_cat = row["category"]
-    if isinstance(raw_cat, int) or (isinstance(raw_cat, str) and raw_cat.isdigit()):
-        idx = int(raw_cat)
-        resolved = _CATEGORY_MAP[idx] if 0 <= idx < len(_CATEGORY_MAP) else "economic"
+    raw_cat = row["category"]
+    if isinstance(raw_cat, int) or (isinstance(raw_cat, str) and raw_cat.isdigit()):
+        idx = int(raw_cat)
+        resolved = _CATEGORY_MAP[idx] if 0 <= idx < len(_CATEGORY_MAP) else "economic"
+    else:
+        resolved = raw_cat
+    return Policy(
+        id=PolicyId(row["policy_id"]),
+        name=row["name"],
+        description=row["description"] or "",
+        category=PolicyCategory(resolved),
+        weights=PolicyWeights(**{k: float(v) for k, v in weights_dict.items()}),
+        is_active=bool(row["is_active"]),
+        enactment_tick=0,
+    )
```

Also add the module-level constant near the top of the file (after imports):

```python
_CATEGORY_MAP = ["economic", "social", "environmental", "public_order",
                 "education", "healthcare", "infrastructure", "cultural"]
```

---

## 2. `frontend/src/services/api.ts` — lines 115, 122

Add trailing slashes to avoid Starlette's 307 redirect (which drops CORS headers):

**Line 115:**
```typescript
-    const response = await apiClient.get<PolicyListResponseDTO>('/policies');
+    const response = await apiClient.get<PolicyListResponseDTO>('/policies/');
```

**Line 122:**
```typescript
-    const response = await apiClient.post<PolicyResponseDTO>('/policies', policyData);
+    const response = await apiClient.post<PolicyResponseDTO>('/policies/', policyData);
```

---

## 3. `frontend/src/pages/dashboard.tsx` — line 235

Add `.catch(() => {})` to prevent unhandled rejection:

```typescript
-    apiService.getPolicies().then((res: any) => setPolicies(res.policies || res));
+    apiService.getPolicies().then((res: any) => setPolicies(res.policies || res)).catch(() => {});
```

---

## 4. `frontend/src/components/dashboard/GovernanceCard.tsx` — lines 17, 43, 109-113

Use string category values matching the StrEnum:

**Line 17:**
```typescript
-  const [newCategory, setNewCategory] = useState(1);
+  const [newCategory, setNewCategory] = useState('economic');
```

**Line 43:**
```typescript
+      const catLabel = newCategory === 'economic' ? 'Economic' : newCategory === 'social' ? 'Social' : 'Public Order';
-      await apiService.createPolicy({ name: newName, description: `${newCategory === 1 ? 'Economic' : 'Social'} policy`, category: newCategory as unknown as PolicyCategory });
+      await apiService.createPolicy({ name: newName, description: `${catLabel} policy`, category: newCategory as unknown as PolicyCategory });
```

**Lines 109-113:**
```typescript
-          <select className="gov-select" value={newCategory} onChange={(e) => setNewCategory(Number(e.target.value))}>
-            <option value={1}>Economic</option>
-            <option value={2}>Social</option>
-            <option value={4}>Public Order</option>
+          <select className="gov-select" value={newCategory} onChange={(e) => setNewCategory(e.target.value)}>
+            <option value="economic">Economic</option>
+            <option value="social">Social</option>
+            <option value="public_order">Public Order</option>
           </select>
```

---

## 5. Delete stale database

```powershell
Remove-Item -LiteralPath "societas.db" -ErrorAction SilentlyContinue
```

---

## Verification

```powershell
# Terminal 1 — backend
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 — test policies endpoint
curl http://localhost:8000/api/v1/policies/

# Terminal 3 — frontend
cd frontend && npm run dev
```

Navigate to the dashboard — no more `ApiError: API 0: Network Error`.
