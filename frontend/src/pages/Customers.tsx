import { useEffect, useState, useCallback } from "react";
import { Plus, Search, Loader2, Pencil, Trash2, Eye, CheckSquare, Square } from "lucide-react";
import { customersApi, batchApi } from "@/api/endpoints";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { PageHeader } from "@/components/app/PageHeader";
import { useAuthStore } from "@/stores/authStore";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import type { Customer, OrderListItem } from "@/types";

const fmt = (v: number) => new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(v);

interface FormData { name: string; company: string; email: string; phone: string; region: string; customer_type: string; }
const emptyForm: FormData = { name: "", company: "", email: "", phone: "", region: "", customer_type: "retail" };

export default function Customers() {
  const user = useAuthStore((state) => state.user);
  const canManage = user?.role.name === "admin" || user?.role.name === "manager";
  const [items, setItems] = useState<Customer[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [regionFilter, setRegionFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [page, setPage] = useState(0);
  const limit = 20;

  const [dialog, setDialog] = useState(false);
  const [editing, setEditing] = useState<Customer | null>(null);
  const [form, setForm] = useState<FormData>(emptyForm);
  const [saving, setSaving] = useState(false);
  const [deleteId, setDeleteId] = useState<number | null>(null);
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [batchDeleting, setBatchDeleting] = useState(false);

  const handleBatchDelete = async () => {
    if (!confirm(`Delete ${selected.size} selected customers?`)) return;
    setBatchDeleting(true);
    try {
      await batchApi.deleteCustomers(Array.from(selected));
      setSelected(new Set());
      fetch();
    } catch (e) { console.error(e); }
    setBatchDeleting(false);
  };
  const [viewCustomer, setViewCustomer] = useState<Customer | null>(null);
  const [viewOrders, setViewOrders] = useState<OrderListItem[]>([]);

  const fetch = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, unknown> = { skip: page * limit, limit };
      if (search) params.search = search;
      if (regionFilter) params.region = regionFilter;
      if (typeFilter) params.customer_type = typeFilter;
      const res = await customersApi.list(params as Parameters<typeof customersApi.list>[0]);
      setItems(res.data.items);
      setTotal(res.data.total);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  }, [search, regionFilter, typeFilter, page]);

  useEffect(() => { fetch(); }, [fetch]);
  const totalPages = Math.max(1, Math.ceil(total / limit));

  const openCreate = () => { setEditing(null); setForm(emptyForm); setDialog(true); };
  const openEdit = (c: Customer) => {
    setEditing(c);
    setForm({ name: c.name, company: c.company || "", email: c.email || "", phone: c.phone || "", region: c.region || "", customer_type: c.customer_type || "retail" });
    setDialog(true);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const data = { ...form, company: form.company || undefined, email: form.email || undefined, phone: form.phone || undefined, region: form.region || undefined, customer_type: form.customer_type || undefined };
      if (editing) await customersApi.update(editing.id, data);
      else await customersApi.create(data);
      setDialog(false);
      fetch();
    } catch (e) { console.error(e); }
    finally { setSaving(false); }
  };

  const handleDelete = async () => {
    if (!deleteId) return;
    try { await customersApi.delete(deleteId); setDeleteId(null); fetch(); } catch (e) { console.error(e); }
  };

  const openView = async (c: Customer) => {
    setViewCustomer(c);
    try {
      const res = await customersApi.getOrders(c.id);
      setViewOrders(Array.isArray(res.data) ? res.data : []);
    } catch { setViewOrders([]); }
  };

  const upd = (field: keyof FormData, value: string) => setForm({ ...form, [field]: value });

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Account management"
        title="Customers"
        description="Manage account profiles, regional ownership, and lifetime commercial value."
        actions={canManage && <Button onClick={openCreate}><Plus className="mr-2 h-4 w-4" />Add customer</Button>}
      />

      <Card>
        <CardContent className="flex flex-wrap items-end gap-3 p-4">
          <div className="min-w-[200px] flex-1">
            <Label className="filter-label">Search</Label>
            <div className="relative">
              <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input className="pl-8" placeholder="Name, email, company..." value={search} onChange={(e) => { setSearch(e.target.value); setPage(0); }} />
            </div>
          </div>
          <div>
            <Label className="filter-label">Region</Label>
            <select className="control-select min-w-[150px]" value={regionFilter} onChange={(e) => { setRegionFilter(e.target.value); setPage(0); }}>
              <option value="">All</option>
              {["North", "South", "East", "West", "Central"].map((r) => <option key={r} value={r}>{r}</option>)}
            </select>
          </div>
          <div>
            <Label className="filter-label">Type</Label>
            <select className="control-select min-w-[160px]" value={typeFilter} onChange={(e) => { setTypeFilter(e.target.value); setPage(0); }}>
              <option value="">All</option>
              <option value="retail">Retail</option><option value="wholesale">Wholesale</option><option value="enterprise">Enterprise</option>
            </select>
          </div>
          <Button variant="ghost" size="sm" onClick={() => { setSearch(""); setRegionFilter(""); setTypeFilter(""); setPage(0); }}>Clear</Button>
        </CardContent>
      </Card>

      {/* Batch action bar */}
      {canManage && selected.size > 0 && (
        <div className="flex items-center gap-3 rounded-lg border bg-blue-50 p-3">
          <span className="text-sm font-medium">{selected.size} selected</span>
          <Button variant="destructive" size="sm" disabled={batchDeleting} onClick={handleBatchDelete}>
            {batchDeleting ? <Loader2 className="mr-1 h-4 w-4 animate-spin" /> : <Trash2 className="mr-1 h-4 w-4" />}
            Delete Selected
          </Button>
          <Button variant="outline" size="sm" onClick={() => setSelected(new Set())}>Clear Selection</Button>
        </div>
      )}

      <Card>
        <CardContent className="p-0">
          {loading ? <div className="flex h-32 items-center justify-center"><Loader2 className="h-6 w-6 animate-spin" /></div> : (
            <Table>
              <TableHeader>
                <TableRow>
                  {canManage && <TableHead className="w-[40px]">
                    <button onClick={() => {
                      if (selected.size === items.length) setSelected(new Set());
                      else setSelected(new Set(items.map(c => c.id)));
                    }}>
                      {selected.size === items.length && items.length > 0 ? <CheckSquare className="h-4 w-4" /> : <Square className="h-4 w-4" />}
                    </button>
                  </TableHead>}
                  <TableHead>Name</TableHead><TableHead>Company</TableHead><TableHead>Email</TableHead><TableHead>Phone</TableHead>
                  <TableHead>Region</TableHead><TableHead>Type</TableHead><TableHead className="text-right">Spending</TableHead><TableHead className="sticky right-0 bg-slate-50 text-right shadow-[-8px_0_12px_-12px_rgb(15_23_42/0.3)]">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {items.length === 0 ? (
                  <TableRow><TableCell colSpan={9} className="text-center text-muted-foreground py-8">No customers found</TableCell></TableRow>
                ) : items.map((c) => (
                  <TableRow key={c.id}>
                    {canManage && <TableCell>
                      <button onClick={() => {
                        const next = new Set(selected);
                        next.has(c.id) ? next.delete(c.id) : next.add(c.id);
                        setSelected(next);
                      }}>
                        {selected.has(c.id) ? <CheckSquare className="h-4 w-4 text-blue-600" /> : <Square className="h-4 w-4 text-muted-foreground" />}
                      </button>
                    </TableCell>}
                    <TableCell className="font-medium">{c.name}</TableCell>
                    <TableCell>{c.company || "—"}</TableCell>
                    <TableCell>{c.email || "—"}</TableCell>
                    <TableCell>{c.phone || "—"}</TableCell>
                    <TableCell>{c.region || "—"}</TableCell>
                    <TableCell><Badge variant="outline">{c.customer_type || "—"}</Badge></TableCell>
                    <TableCell className="text-right">{fmt(c.total_spending)}</TableCell>
                    <TableCell className="sticky right-0 bg-white text-right shadow-[-8px_0_12px_-12px_rgb(15_23_42/0.3)]">
                      <div className="inline-flex rounded-lg border border-slate-200 bg-white p-0.5 shadow-sm">
                        <Button title="View customer" variant="ghost" size="icon" className="icon-action h-7 w-7" onClick={() => openView(c)}><Eye className="h-3.5 w-3.5" /></Button>
                        {canManage && <Button title="Edit customer" variant="ghost" size="icon" className="icon-action h-7 w-7" onClick={() => openEdit(c)}><Pencil className="h-3.5 w-3.5" /></Button>}
                        {canManage && <Button title="Delete customer" variant="ghost" size="icon" className="h-7 w-7 text-slate-400 hover:bg-red-50 hover:text-red-600" onClick={() => setDeleteId(c.id)}><Trash2 className="h-3.5 w-3.5" /></Button>}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">{total} total customers</p>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" disabled={page === 0} onClick={() => setPage(page - 1)}>Previous</Button>
          <span className="flex items-center text-sm">Page {page + 1} of {totalPages}</span>
          <Button variant="outline" size="sm" disabled={page >= totalPages - 1} onClick={() => setPage(page + 1)}>Next</Button>
        </div>
      </div>

      {/* View Dialog */}
      <Dialog open={!!viewCustomer} onOpenChange={() => setViewCustomer(null)}>
        <DialogContent className="max-w-lg">
          <DialogHeader><DialogTitle>{viewCustomer?.name}</DialogTitle></DialogHeader>
          {viewCustomer && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div><span className="text-muted-foreground">Company:</span> {viewCustomer.company || "—"}</div>
                <div><span className="text-muted-foreground">Email:</span> {viewCustomer.email || "—"}</div>
                <div><span className="text-muted-foreground">Phone:</span> {viewCustomer.phone || "—"}</div>
                <div><span className="text-muted-foreground">Region:</span> {viewCustomer.region || "—"}</div>
                <div><span className="text-muted-foreground">Type:</span> {viewCustomer.customer_type || "—"}</div>
                <div><span className="text-muted-foreground">Total Spending:</span> {fmt(viewCustomer.total_spending)}</div>
              </div>
              <div>
                <h4 className="mb-2 text-sm font-medium">Order History</h4>
                {viewOrders.length === 0 ? <p className="text-sm text-muted-foreground">No orders yet</p> : (
                  <Table>
                    <TableHeader><TableRow><TableHead>ID</TableHead><TableHead>Date</TableHead><TableHead className="text-right">Amount</TableHead><TableHead>Status</TableHead></TableRow></TableHeader>
                    <TableBody>
                      {viewOrders.map((o) => (
                        <TableRow key={o.id}>
                          <TableCell>#{o.id}</TableCell>
                          <TableCell>{new Date(o.order_date).toLocaleDateString()}</TableCell>
                          <TableCell className="text-right">{fmt(o.total_amount)}</TableCell>
                          <TableCell><Badge variant={o.payment_status === "paid" ? "default" : "secondary"}>{o.payment_status}</Badge></TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Create/Edit Dialog */}
      <Dialog open={dialog} onOpenChange={setDialog}>
        <DialogContent>
          <DialogHeader><DialogTitle>{editing ? "Edit Customer" : "Add Customer"}</DialogTitle></DialogHeader>
          <div className="grid grid-cols-2 gap-3">
            <div><Label>Name *</Label><Input value={form.name} onChange={(e) => upd("name", e.target.value)} /></div>
            <div><Label>Company</Label><Input value={form.company} onChange={(e) => upd("company", e.target.value)} /></div>
            <div><Label>Email</Label><Input type="email" value={form.email} onChange={(e) => upd("email", e.target.value)} /></div>
            <div><Label>Phone</Label><Input value={form.phone} onChange={(e) => upd("phone", e.target.value)} /></div>
            <div><Label>Region</Label>
              <select className="h-9 w-full rounded-md border bg-background px-3 text-sm" value={form.region} onChange={(e) => upd("region", e.target.value)}>
                <option value="">Select...</option>
                {["North", "South", "East", "West", "Central"].map((r) => <option key={r} value={r}>{r}</option>)}
              </select>
            </div>
            <div><Label>Type</Label>
              <select className="h-9 w-full rounded-md border bg-background px-3 text-sm" value={form.customer_type} onChange={(e) => upd("customer_type", e.target.value)}>
                <option value="retail">Retail</option><option value="wholesale">Wholesale</option><option value="enterprise">Enterprise</option>
              </select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDialog(false)}>Cancel</Button>
            <Button onClick={handleSave} disabled={saving || !form.name}>
              {saving ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Saving...</> : "Save"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete */}
      <Dialog open={!!deleteId} onOpenChange={() => setDeleteId(null)}>
        <DialogContent>
          <DialogHeader><DialogTitle>Delete Customer</DialogTitle></DialogHeader>
          <p className="text-sm text-muted-foreground">Are you sure you want to delete this customer?</p>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteId(null)}>Cancel</Button>
            <Button variant="destructive" onClick={handleDelete}>Delete</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
