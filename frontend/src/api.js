const API_ROOT = "/api";

async function request(path, options = {}) {
  const response = await fetch(`${API_ROOT}${path}`, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(payload.detail || "Request failed");
  }
  return response.json();
}

export const api = {
  listTenants: () => request(`/tenants`),
  overview: (tenantId) => request(`/overview?tenant_id=${encodeURIComponent(tenantId)}`),
  listClaims: (tenantId) => request(`/claims?tenant_id=${encodeURIComponent(tenantId)}`),
  claimDetail: (claimId) => request(`/claims/${claimId}`),
  validateClaim: (claimId) => request(`/claims/${claimId}/validate`, { method: "POST" }),
  fraudCheck: (claimId) => request(`/claims/${claimId}/fraud-check`, { method: "POST" }),
  adjudicateClaim: (claimId) => request(`/claims/${claimId}/adjudicate`, { method: "POST" }),
  createClaim: (payload) => request(`/claims`, { method: "POST", body: JSON.stringify(payload) }),
};
