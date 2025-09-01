import React, { useEffect, useMemo, useRef, useState } from "react";
import { motion } from "framer-motion";
import {
  Box,
  Container,
  Typography,
  Card,
  CardHeader,
  CardContent,
  CardActions,
  TextField,
  Button,
  Chip,
  Stack,
  Divider,
  Alert,
  AlertTitle,
  InputAdornment,
  Skeleton,
  IconButton,
  CircularProgress,
} from "@mui/material";
import {
  Search,
  BookOpen,
  Loader2,
  Sparkles,
  Stars,
  Copy,
  Check,
  RotateCcw,
  XCircle,
} from "lucide-react";


const API_URL = "http://localhost:8000/chat";

type ChatResult = { title: string; reason: string; summary: string } | null;

export default function SmartLibrarianApp() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [result, setResult] = useState<ChatResult>(null);

  async function onAsk(e?: React.FormEvent) {
    e?.preventDefault();
    setCopied(false);
    setError(null);
    const q = query.trim();
    if (!q) {
      setError("Write a question about books.");
      return;
    }
    try {
      setLoading(true);
      setResult(null);
      const res = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: q }),
      });
      if (!res.ok) {
        const txt = await res.text();
        throw new Error(`HTTP ${res.status}: ${txt}`);
      }
      const data = await res.json();
      setResult({
        title: data.title ?? "(no title)",
        reason: data.reason ?? "",
        summary: data.summary ?? "",
      });
    } catch (err: any) {
      setError(err?.message || "An error occurred.");
    } finally {
      setLoading(false);
    }
  }

  // Keyboard: Cmd/Ctrl+Enter submits
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "enter") {
        onAsk();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [query]);

  function onReset() {
    setQuery("");
    setResult(null);
    setError(null);
    setCopied(false);
    inputRef.current?.focus();
  }

  async function copyAll() {
    if (!result) return;
    const blob = `Title: ${result.title}\n\nReason: ${result.reason}\n\nSummary:\n${result.summary}`;
    await navigator.clipboard.writeText(blob);
    setCopied(true);
    setTimeout(() => setCopied(false), 1800);
  }

  return (
    <Box sx={{minHeight: "100vh", minWidth: "100vw", bgcolor: "background.default" }}>
      <Box
        sx={{
          position: "fixed",
          inset: 0,
          zIndex: -1,
          background:
            "radial-gradient(1200px 600px at 10% -10%, rgba(56,189,248,0.10), transparent), radial-gradient(800px 500px at 90% 10%, rgba(167,139,250,0.10), transparent)",
        }}
      />

      <Container maxWidth="md" sx={{ pt: 8, pb: 10 }}>
        <header>
          <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
            <Stack direction="row" spacing={1.5} alignItems="center" sx={{ mb: 0.5 }}>
              <Box sx={{ p: 1, borderRadius: 3, bgcolor: "primary.light", color: "primary.contrastText", display: "inline-flex" }}>
                <Sparkles size={22} />
              </Box>
              <Typography
                component="h1"
                variant="h4"
                sx={{
                  fontWeight: 600,
                  background: (t) => `linear-gradient(90deg, ${t.palette.text.primary}, ${t.palette.text.secondary})`,
                  WebkitBackgroundClip: "text",
                  WebkitTextFillColor: "transparent",
                }}
              >
                Smart Librarian
              </Typography>
            </Stack>
            <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
              Search for a book recommendation based on your themes. (RAG + tool)
            </Typography>
          </motion.div>
        </header>

        <main>
            <Card variant="outlined" sx={{ backdropFilter: "saturate(120%) blur(4px)" }}>
              <CardHeader title="Question" subheader="Describe the desired themes, tone, or genres." />
            <CardContent>
              <form onSubmit={onAsk}>
                <Stack direction={{ xs: "column", sm: "row" }} spacing={1.5} alignItems={{ sm: "stretch" }}>
                  <TextField
                    fullWidth
                    inputRef={inputRef}
                    placeholder="ex: ‘I want a book about friendship and magic’"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    InputProps={{
                      startAdornment: (
                        <InputAdornment position="start">
                          <Search size={18} />
                        </InputAdornment>
                      ),
                    }}
                  />

                  <Stack direction="row" spacing={1} justifyContent="flex-end">
                    <Button
                      type="submit"
                      variant="contained"
                      size="large"
                      startIcon={!loading ? <BookOpen size={18} /> : undefined}
                      disabled={loading}
                      onClick={onAsk}
                    >
                      {loading ? (
                        <>
                          <CircularProgress size={20} sx={{ mr: 1 }} /> Caut…
                        </>
                      ) : (
                        "Recommend"
                      )}
                    </Button>
                    <Button type="button" variant="outlined" size="large" startIcon={<RotateCcw size={18} />} onClick={onReset}>
                      Reset
                    </Button>
                  </Stack>
                </Stack>

                <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: "block" }}>
                  shortcut: Ctrl/Cmd + Enter
                </Typography>

                {error && (
                  <Alert severity="error" sx={{ mt: 1.5 }} icon={<XCircle size={18} />}>
                    <AlertTitle>Error</AlertTitle>
                    {error}
                  </Alert>
                )}
              </form>
            </CardContent>
          </Card>

          {/* Results */}
          <Box sx={{ mt: 2 }}>
            {loading && <SkeletonResult />}

            {result && (
              <motion.section initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35 }}>
                <Stack spacing={2}>
                  <Card variant="outlined">
                    <CardHeader
                      title="Recomandation"
                      subheader=""
                    />
                    <CardContent>
                      <Typography variant="h5" sx={{ fontWeight: 600 }}>
                        {result.title}
                      </Typography>
                      {result.reason && (
                        <Typography variant="body1" sx={{ mt: 1.5 }}>
                          <strong>Why:</strong> {result.reason}
                        </Typography>
                      )}
                    </CardContent>
                    <CardActions sx={{ pt: 0, pb: 2, px: 2 }}>
                      <Button variant="outlined" size="small" onClick={copyAll} startIcon={copied ? <Check size={18} /> : <Copy size={18} />}>
                        {copied ? "Copied" : "Copy"}
                      </Button>
                    </CardActions>
                  </Card>

                  <Card variant="outlined">
                    <CardHeader title="Detailed summary." />
                    <CardContent>
                      <Typography sx={{ whiteSpace: "pre-wrap", lineHeight: 1.7 }}>{result.summary}</Typography>
                      <Divider sx={{ my: 2 }} />
                      
                    </CardContent>
                  </Card>
                </Stack>
              </motion.section>
            )}

            {!loading && !result && !error && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.05 }}>
                <Typography variant="body2" color="text.secondary">
                  Suggestions: "A dystopian but optimistic book", "War and psychological consequences", "Mystery & crime with magical elements".
                </Typography>
              </motion.div>
            )}
          </Box>
        </main>

        <footer>
          <Divider sx={{ my: 4 }} />
          <Typography variant="caption" color="text.secondary" display="block">
            © {new Date().getFullYear()} Smart Librarian — UI: MUI + Framer Motion
          </Typography>
          <Typography variant="caption" color="text.secondary" display="block">
            DavaX
          </Typography>
        </footer>

      </Container>
    </Box>
  );
}


function SkeletonResult() {
  return (
    <Card variant="outlined" sx={{ p: 2 }}>
      <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 1 }}>
        <Loader2 size={18} />
        <Typography variant="subtitle1">Analyzing your themes...</Typography>
      </Stack>
      <Skeleton height={16} width="70%" />
      <Skeleton height={16} />
      <Skeleton height={16} width="85%" />
      <Divider sx={{ my: 2 }} />
      <Skeleton height={16} />
      <Skeleton height={16} width="60%" />
    </Card>
  );
}
