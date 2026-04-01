import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Swal from "sweetalert2";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { getStoredProfile } from "@/lib/profile-session";
import { getHistory } from "@/services/api";
import type { HistoryItem, Profile } from "@/types/types";

const HistoryPage: React.FC = () => {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [zoneFilter, setZoneFilter] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    setProfile(getStoredProfile());
  }, []);

  useEffect(() => {
    if (!profile) {
      return;
    }
    const load = async () => {
      setIsLoading(true);
      try {
        const response = await getHistory(profile.id, {
          zone: zoneFilter,
          dateFrom,
          dateTo,
          page,
          pageSize: 10,
        });
        setItems(response.items);
        setPage(response.page);
        setTotalPages(response.total_pages);
        setTotal(response.total);
      } catch (error: any) {
        await Swal.fire({
          icon: "error",
          title: "History Error",
          text: error?.response?.data?.detail || "Could not load profile history.",
          confirmButtonColor: "#0b4f4a",
        });
      } finally {
        setIsLoading(false);
      }
    };
    void load();
  }, [profile, zoneFilter, dateFrom, dateTo, page]);

  if (!profile) {
    return (
      <div className="min-h-screen bg-[linear-gradient(180deg,rgba(11,79,74,0.08),rgba(255,255,255,0))] p-6">
        <Card className="mx-auto max-w-2xl border-teal-100 shadow-sm">
          <CardHeader>
            <CardTitle className="text-teal-950">No Profile Selected</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-muted-foreground">
              Select a profile first so history can be scoped correctly.
            </p>
            <div className="flex gap-3">
              <Link to="/">
                <Button className="bg-teal-950 hover:bg-teal-900">Back to Upload</Button>
              </Link>
              <Link to="/profiles/select">
                <Button variant="outline" className="border-teal-200 text-teal-900 hover:bg-teal-50">Select Profile</Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[linear-gradient(180deg,rgba(11,79,74,0.08),rgba(255,255,255,0))] p-4 md:p-8">
      <div className="mx-auto flex max-w-5xl flex-col gap-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-semibold text-teal-950">History</h1>
            <p className="text-muted-foreground">
              Showing report runs for {profile.name}.
            </p>
          </div>
          <div className="flex gap-3">
            <Link to="/">
              <Button variant="outline" className="border-teal-200 text-teal-900 hover:bg-teal-50">Back to Upload</Button>
            </Link>
            <Link to="/profiles/select">
              <Button variant="outline" className="border-teal-200 text-teal-900 hover:bg-teal-50">Change Profile</Button>
            </Link>
          </div>
        </div>

        <Card className="border-teal-100 shadow-sm">
          <CardHeader>
            <CardTitle className="text-teal-950">Filters</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4 md:grid-cols-3">
            <Input
              placeholder="Filter by zone"
              value={zoneFilter}
              onChange={(event) => {
                setZoneFilter(event.target.value);
                setPage(1);
              }}
            />
            <Input
              type="date"
              value={dateFrom}
              onChange={(event) => {
                setDateFrom(event.target.value);
                setPage(1);
              }}
            />
            <Input
              type="date"
              value={dateTo}
              onChange={(event) => {
                setDateTo(event.target.value);
                setPage(1);
              }}
            />
          </CardContent>
        </Card>

        <Card className="border-teal-100 shadow-sm">
          <CardHeader>
            <CardTitle className="text-teal-950">Processed Zones</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="space-y-3">
                <Skeleton className="h-10 w-full" />
                <Skeleton className="h-10 w-full" />
                <Skeleton className="h-10 w-full" />
              </div>
            ) : items.length === 0 ? (
              <p className="text-muted-foreground">
                No report runs found for this profile yet.
              </p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead>
                    <tr className="border-b">
                      <th className="px-2 py-3 font-medium">Zone</th>
                      <th className="px-2 py-3 font-medium">Source File</th>
                      <th className="px-2 py-3 font-medium">Status</th>
                      <th className="px-2 py-3 font-medium">Period</th>
                      <th className="px-2 py-3 font-medium">Created</th>
                      <th className="px-2 py-3 font-medium">Error</th>
                    </tr>
                  </thead>
                  <tbody>
                    {items.map((item) => (
                      <tr key={item.id} className="border-b align-top">
                        <td className="px-2 py-3">{item.zone_name}</td>
                        <td className="px-2 py-3">{item.source_filename}</td>
                        <td className="px-2 py-3 capitalize">{item.status}</td>
                        <td className="px-2 py-3">{item.detected_period_label ?? "n/a"}</td>
                        <td className="px-2 py-3">
                          {new Date(item.created_at).toLocaleString()}
                        </td>
                        <td className="px-2 py-3 text-muted-foreground">
                          {item.error_message ?? "-"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            <div className="mt-4 flex items-center justify-between border-t pt-4 text-sm text-muted-foreground">
              <p>
                Showing page {page} of {totalPages} - {total} total runs
              </p>
              <div className="flex gap-3">
                <Button
                  type="button"
                  variant="outline"
                  className="border-teal-200 text-teal-900 hover:bg-teal-50"
                  disabled={page <= 1 || isLoading}
                  onClick={() => setPage((current) => Math.max(current - 1, 1))}
                >
                  Previous
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  className="border-teal-200 text-teal-900 hover:bg-teal-50"
                  disabled={page >= totalPages || isLoading}
                  onClick={() => setPage((current) => Math.min(current + 1, totalPages))}
                >
                  Next
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default HistoryPage;
