import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { getStoredProfile, setStoredProfile } from "@/lib/profile-session";
import { searchProfiles } from "@/services/api";
import type { Profile } from "@/types/types";

const SelectProfilePage: React.FC = () => {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const stored = getStoredProfile();
    if (stored) {
      setQuery(stored.name);
    }
  }, []);

  useEffect(() => {
    const loadProfiles = async () => {
      setIsLoading(true);
      try {
        const result = await searchProfiles(query.trim());
        setProfiles(result);
      } finally {
        setIsLoading(false);
      }
    };
    void loadProfiles();
  }, [query]);

  return (
    <div className="min-h-screen bg-background p-6">
      <Card className="mx-auto max-w-3xl">
        <CardHeader>
          <CardTitle>Select Profile</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex flex-col gap-3 sm:flex-row">
            <Input
              placeholder="Search profiles by name"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
            />
            <Link to="/profiles/new">
              <Button>Create New Profile</Button>
            </Link>
          </div>

          {isLoading ? (
            <div className="space-y-3">
              <Skeleton className="h-14 w-full" />
              <Skeleton className="h-14 w-full" />
              <Skeleton className="h-14 w-full" />
            </div>
          ) : profiles.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No matching profiles found yet. Create one to continue.
            </p>
          ) : (
            <div className="space-y-3">
              {profiles.map((profile) => (
                <button
                  key={profile.id}
                  type="button"
                  onClick={() => {
                    setStoredProfile(profile);
                    navigate("/");
                  }}
                  className="flex w-full items-center justify-between rounded-lg border p-4 text-left transition-colors hover:bg-muted/40"
                >
                  <div>
                    <p className="font-medium">{profile.name}</p>
                    <p className="text-sm text-muted-foreground">
                      {profile.email || "No email provided"}
                    </p>
                  </div>
                  <span className="text-sm text-muted-foreground">Use profile</span>
                </button>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default SelectProfilePage;

