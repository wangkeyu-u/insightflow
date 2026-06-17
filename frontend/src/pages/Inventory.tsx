import { Warehouse } from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export default function Inventory() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Inventory Management</h1>
        <p className="text-muted-foreground">
          Stock levels and warehouse management
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Inventory Management</CardTitle>
          <CardDescription>
            Inventory tracking and stock management
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center rounded-lg border border-dashed p-12 text-center">
            <Warehouse className="mb-4 h-12 w-12 text-muted-foreground" />
            <p className="text-sm text-muted-foreground">
              Inventory tracking coming soon. Monitor stock levels, low-stock alerts, and warehouse management.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
