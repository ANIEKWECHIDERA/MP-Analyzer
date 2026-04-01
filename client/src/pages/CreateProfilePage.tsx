import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import Swal from "sweetalert2";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { setStoredProfile } from "@/lib/profile-session";
import { createProfile } from "@/services/api";
import { Loader2 } from "lucide-react";

const CreateProfilePage: React.FC = () => {
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [isSaving, setIsSaving] = useState(false);

  const handleCreate = async (event: React.FormEvent) => {
    event.preventDefault();

    if (!name.trim()) {
      await Swal.fire({
        icon: "warning",
        title: "Name Required",
        text: "Please enter a name to create a profile.",
        confirmButtonColor: "#0b4f4a",
      });
      return;
    }

    setIsSaving(true);
    try {
      const profile = await createProfile({
        name: name.trim(),
        email: email.trim() || undefined,
      });
      setStoredProfile(profile);
      navigate("/");
    } catch (error: any) {
      await Swal.fire({
        icon: "error",
        title: "Profile Error",
        text: error?.response?.data?.detail || "Unable to create the profile.",
        confirmButtonColor: "#0b4f4a",
      });
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-[linear-gradient(180deg,rgba(11,79,74,0.08),rgba(255,255,255,0))] p-6">
      <Card className="mx-auto max-w-2xl border-teal-100 shadow-sm">
        <CardHeader>
          <CardTitle className="text-teal-950">Create New Profile</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleCreate} className="space-y-4">
            <Input
              placeholder="Name"
              value={name}
              onChange={(event) => setName(event.target.value)}
            />
            <Input
              placeholder="Email (optional)"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
            <div className="flex gap-3">
              <Button type="submit" disabled={isSaving} className="bg-teal-950 hover:bg-teal-900">
                {isSaving ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Creating Profile...
                  </>
                ) : (
                  "Create Profile"
                )}
              </Button>
              <Link to="/profiles/select">
                <Button
                  type="button"
                  variant="outline"
                  className="border-teal-200 text-teal-900 hover:bg-teal-50"
                >
                  Back to Select
                </Button>
              </Link>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};

export default CreateProfilePage;
