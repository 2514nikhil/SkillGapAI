"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { analyzeResume, getRoles } from "@/lib/api";
import { RoleItem } from "@/lib/types";
import Tour from "@/components/Tour";
import Hint from "@/components/Hint";
import { TourStep } from "@/lib/tourUtils";

const uploadTourSteps: TourStep[] = [
  {
    target: '[data-tour="resume-file"]',
    title: "Resume file",
    body: "Upload your resume as a PDF or DOCX. Scanned images will not work because we need to read the text.",
    placement: "bottom",
  },
  {
    target: '[data-tour="target-role"]',
    title: "Target role",
    body: "Pick the job you want. The skills needed come from real job postings for that role.",
    placement: "bottom",
  },
  {
    target: '[data-tour="job-description"]',
    title: "Job description box",
    body: "Have a specific job in mind? Paste its description here instead and we will compare against that.",
    placement: "top",
  },
  {
    target: '[data-tour="analyze-button"]',
    title: "Analyze button",
    body: "Press this when you are ready. It usually takes a few seconds. Your resume is not saved.",
    placement: "top",
  },
];

export default function UploadPage() {
  const router = useRouter();

  const [roles, setRoles] = useState<RoleItem[]>([]);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedRole, setSelectedRole] = useState<string>("");
  const [jobDescription, setJobDescription] = useState<string>("");

  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [fileError, setFileError] = useState<string | null>(null);
  const [targetError, setTargetError] = useState<string | null>(null);
  const [apiError, setApiError] = useState<string | null>(null);

  useEffect(() => {
    // Load available roles from the API
    getRoles()
      .then((data) => {
        setRoles(data);
      })
      .catch((err) => {
        setApiError(err instanceof Error ? err.message : "The server is waking up. Try again in a minute.");
      });
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFileError(null);
    setApiError(null);
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      const ext = file.name.split(".").pop()?.toLowerCase();
      if (!ext || !["pdf", "docx", "txt"].includes(ext)) {
        setFileError("Please select a PDF, DOCX, or plain text file.");
        setSelectedFile(null);
        return;
      }
      if (file.size > 5 * 1024 * 1024) {
        setFileError("File exceeds maximum allowed size of 5 MB.");
        setSelectedFile(null);
        return;
      }
      setSelectedFile(file);
    } else {
      setSelectedFile(null);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFileError(null);
    setTargetError(null);
    setApiError(null);

    let hasError = false;

    if (!selectedFile) {
      setFileError("Please choose a resume file to upload.");
      hasError = true;
    }

    const trimmedJd = jobDescription.trim();
    if (!selectedRole && !trimmedJd) {
      setTargetError("Please select a target role or paste a job description.");
      hasError = true;
    }

    if (hasError || !selectedFile) {
      return;
    }

    setIsAnalyzing(true);

    try {
      const formData = new FormData();
      formData.append("file", selectedFile);

      if (selectedRole) {
        formData.append("role", selectedRole);
      } else if (trimmedJd) {
        formData.append("jd", trimmedJd);
      }

      const response = await analyzeResume(formData);

      // Store response in sessionStorage for /result page
      if (typeof window !== "undefined") {
        sessionStorage.setItem("skillgap_result", JSON.stringify(response));
        sessionStorage.setItem("skillgap_target_role", selectedRole || "Custom Job Description");
      }

      router.push("/result");
    } catch (err: unknown) {
      setIsAnalyzing(false);
      if (err instanceof Error) {
        setApiError(err.message);
      } else {
        setApiError("An unexpected error occurred during analysis.");
      }
    }
  };

  return (
    <div>
      <Tour steps={uploadTourSteps} storageKey="skillgap_tour_upload_v1" />

      <h1>SkillGap</h1>
      <p>
        Upload your resume to compare your skills against real job postings, find missing skills, and get a practical learning path.
      </p>

      {apiError && (
        <div className="error-box" role="alert">
          {apiError}
        </div>
      )}

      <form onSubmit={handleSubmit} style={{ marginTop: "24px" }} noValidate>
        <div data-tour="resume-file" style={{ marginBottom: "20px" }}>
          <label htmlFor="resume-file">Resume (PDF or DOCX)</label>
          <input
            id="resume-file"
            type="file"
            accept=".pdf,.docx,.txt"
            onChange={handleFileChange}
            aria-describedby={fileError ? "file-error-msg" : undefined}
          />
          {fileError && (
            <div id="file-error-msg" className="field-error">
              {fileError}
            </div>
          )}
        </div>

        <div data-tour="target-role" style={{ marginBottom: "20px" }}>
          <label htmlFor="target-role">Target role</label>
          <select
            id="target-role"
            value={selectedRole}
            onChange={(e) => {
              setSelectedRole(e.target.value);
              setTargetError(null);
            }}
            aria-describedby={targetError ? "target-error-msg" : undefined}
          >
            <option value="">-- Select a target role --</option>
            {roles.map((r) => (
              <option key={r.role} value={r.role}>
                {r.role} ({r.postings_count} postings)
              </option>
            ))}
          </select>
        </div>

        <div data-tour="job-description" style={{ marginBottom: "24px" }}>
          <div style={{ display: "flex", alignItems: "baseline", flexWrap: "wrap", marginBottom: "6px" }}>
            <label htmlFor="job-description" style={{ marginBottom: 0 }}>
              Or paste a job description
            </label>
            <Hint label="What's this?">
              If you paste a job description, the role dropdown is ignored.
            </Hint>
          </div>
          <textarea
            id="job-description"
            rows={5}
            value={jobDescription}
            onChange={(e) => {
              setJobDescription(e.target.value);
              setTargetError(null);
            }}
            placeholder="Paste raw requirements or job posting text here if not selecting a role above..."
          />
          {targetError && (
            <div id="target-error-msg" className="field-error">
              {targetError}
            </div>
          )}
        </div>

        <div data-tour="analyze-button">
          <button type="submit" disabled={isAnalyzing}>
            {isAnalyzing ? "Analyzing..." : "Analyze"}
          </button>
        </div>
      </form>
    </div>
  );
}
