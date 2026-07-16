import React, { useState } from "react";
import {
  Box,
  Typography,
  Paper,
  Tabs,
  Tab,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Chip,
  Grid2 as Grid,
  Card,
  CardContent,
  Divider,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Alert,
} from "@mui/material";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import StorageIcon from "@mui/icons-material/Storage";
import SmartToyIcon from "@mui/icons-material/SmartToy";
import ChatIcon from "@mui/icons-material/Chat";
import SpeedIcon from "@mui/icons-material/Speed";
import BoltIcon from "@mui/icons-material/Bolt";
import CodeIcon from "@mui/icons-material/Code";
import TipsAndUpdatesIcon from "@mui/icons-material/TipsAndUpdates";
import SecurityIcon from "@mui/icons-material/Security";
import HelpOutlineIcon from "@mui/icons-material/HelpOutline";
import UploadFileIcon from "@mui/icons-material/UploadFile";
import DownloadIcon from "@mui/icons-material/Download";

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel({ children, value, index }: TabPanelProps) {
  return (
    <div hidden={value !== index} role="tabpanel">
      {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
    </div>
  );
}

function SectionCard({
  icon,
  title,
  children,
}: {
  icon: React.ReactNode;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <Card variant="outlined" sx={{ height: "100%" }}>
      <CardContent>
        <Box display="flex" alignItems="center" gap={1} mb={1.5}>
          {icon}
          <Typography variant="h6">{title}</Typography>
        </Box>
        {children}
      </CardContent>
    </Card>
  );
}

export default function Documentation() {
  const [tab, setTab] = useState(0);

  return (
    <Box>
      <Box mb={3}>
        <Typography variant="h4" gutterBottom>
          Documentation
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Everything you need to know to connect a PostgreSQL database, add an LLM model, and start
          chatting with your data in plain English.
        </Typography>
      </Box>

      <Paper variant="outlined" sx={{ mb: 3 }}>
        <Tabs
          value={tab}
          onChange={(_, v) => setTab(v)}
          variant="scrollable"
          scrollButtons="auto"
          allowScrollButtonsMobile
        >
          <Tab label="Overview" />
          <Tab label="Getting Started" />
          <Tab label="What the Chatbot Can Do" />
          <Tab label="Writing Good Prompts" />
          <Tab label="Query Optimization" />
          <Tab label="Safety & Best Practices" />
          <Tab label="FAQ" />
        </Tabs>
      </Paper>

      {/* Overview */}
      <TabPanel value={tab} index={0}>
        <Grid container spacing={2}>
          <Grid size={{ xs: 12, md: 6 }}>
            <SectionCard icon={<StorageIcon color="primary" />} title="How this app works">
              <Typography variant="body2" paragraph>
                This app lets you connect one or more PostgreSQL databases and talk to them using
                natural language instead of writing raw SQL by hand. Under the hood, a chat
                request is routed to a team of specialized AI agents:
              </Typography>
              <Box component="ul" sx={{ pl: 2, m: 0 }}>
                <li>
                  <Typography variant="body2">
                    <strong>SQL Agent</strong> — turns your request into SQL (SELECT, INSERT,
                    UPDATE, DELETE, CREATE, ALTER, DROP) and executes it against your database.
                    It can also generate a visual <strong>ER diagram</strong> of your tables and
                    look up the exact <strong>DDL/definition</strong> of a table, view, function,
                    procedure, trigger, sequence, or index.
                  </Typography>
                </li>
                <li>
                  <Typography variant="body2">
                    <strong>Explain Plan Agent</strong> — fetches and explains PostgreSQL's{" "}
                    <code>EXPLAIN</code> execution plan for a query in plain English.
                  </Typography>
                </li>
                <li>
                  <Typography variant="body2">
                    <strong>Optimization Agent</strong> — analyzes a query's plan and suggests
                    indexes and rewrites to make it faster.
                  </Typography>
                </li>
                <li>
                  <Typography variant="body2">
                    <strong>Documentation Agent</strong> — answers questions about your schema
                    itself (tables, columns, relationships) and about the business meaning of
                    your data, drawing on both live database comments and any <code>.sql</code>{" "}
                    files or images you've uploaded for that connection.
                  </Typography>
                </li>
                <li>
                  <Typography variant="body2">
                    <strong>Fallback Agent</strong> — politely redirects anything unrelated to
                    your database back on topic.
                  </Typography>
                </li>
              </Box>
              <Typography variant="body2" sx={{ mt: 1.5 }}>
                An orchestrator picks the right agent (or sequence of agents) for each message,
                so you never have to know which "mode" to pick — just ask.
              </Typography>
            </SectionCard>
          </Grid>

          <Grid size={{ xs: 12, md: 6 }}>
            <SectionCard icon={<BoltIcon color="primary" />} title="How it helps your day-to-day work">
              <Box component="ul" sx={{ pl: 2, m: 0 }}>
                <li>
                  <Typography variant="body2">
                    Skip writing boilerplate <code>SELECT</code>/<code>JOIN</code> statements —
                    describe what you want and let the agent generate correct, schema-aware SQL.
                  </Typography>
                </li>
                <li>
                  <Typography variant="body2">
                    Explore an unfamiliar database quickly ("what tables exist?", "describe the
                    orders table") without digging through a DB client.
                  </Typography>
                </li>
                <li>
                  <Typography variant="body2">
                    Diagnose slow queries and get concrete index/rewrite suggestions without being
                    a PostgreSQL internals expert.
                  </Typography>
                </li>
                <li>
                  <Typography variant="body2">
                    Run one-off data fixes (updates/deletes/inserts) conversationally, with the
                    exact SQL always shown back to you for transparency.
                  </Typography>
                </li>
                <li>
                  <Typography variant="body2">
                    Keep a running conversation/session per database, so follow-up questions
                    ("now filter that by last month") keep context.
                  </Typography>
                </li>
              </Box>
            </SectionCard>
          </Grid>

          <Grid size={{ xs: 12 }}>
            <SectionCard icon={<SpeedIcon color="primary" />} title="How it makes you more efficient">
              <Grid container spacing={2}>
                <Grid size={{ xs: 12, sm: 4 }}>
                  <Typography variant="subtitle2">Less context switching</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Stay in one chat window instead of jumping between a SQL client, docs, and
                    query-plan visualizers.
                  </Typography>
                </Grid>
                <Grid size={{ xs: 12, sm: 4 }}>
                  <Typography variant="subtitle2">Faster iteration</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Refine a query in follow-up messages ("add a WHERE clause", "sort by date")
                    instead of retyping full SQL each time.
                  </Typography>
                </Grid>
                <Grid size={{ xs: 12, sm: 4 }}>
                  <Typography variant="subtitle2">Built-in expertise</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Get PostgreSQL-idiomatic SQL (CTEs, window functions, <code>RETURNING</code>,
                    identity columns) without memorizing syntax.
                  </Typography>
                </Grid>
              </Grid>
            </SectionCard>
          </Grid>
        </Grid>
      </TabPanel>

      {/* Getting Started */}
      <TabPanel value={tab} index={1}>
        <SectionCard icon={<ChatIcon color="primary" />} title="Steps required before you can chat">
          <Stepper orientation="vertical" nonLinear activeStep={-1}>
            <Step expanded>
              <StepLabel>Import a PostgreSQL database</StepLabel>
              <StepContent>
                <Typography variant="body2">
                  Go to the <strong>Databases</strong> tab and click <strong>Import Database</strong>.
                  Enter the host, port, database name, username, password, and SSL mode. Your
                  password is encrypted at rest and never displayed again — the connection is
                  tested immediately and marked <Chip size="small" label="Reachable" color="success" />{" "}
                  if successful.
                </Typography>
              </StepContent>
            </Step>
            <Step expanded>
              <StepLabel>Add an LLM model</StepLabel>
              <StepContent>
                <Typography variant="body2">
                  Go to the <strong>LLM Models</strong> tab and add a model configuration
                  (provider + API key + model name). This is <strong>mandatory</strong> — the
                  chat input stays disabled until at least one LLM model is configured, since the
                  agents need a model to reason with.
                </Typography>
              </StepContent>
            </Step>
            <Step expanded>
              <StepLabel>Open Chat from a database card</StepLabel>
              <StepContent>
                <Typography variant="body2">
                  On the Databases page, click <strong>Chat</strong> on the database you want to
                  talk to, pick which LLM model to use from the dropdown, and start typing.
                </Typography>
              </StepContent>
            </Step>
            <Step expanded>
              <StepLabel>(Optional) Check database health</StepLabel>
              <StepContent>
                <Typography variant="body2">
                  Use the refresh icon on a database card to view approximate CPU usage, cache
                  hit ratio, disk I/O, disk usage, and active connections — all derived from
                  Postgres-native statistics views, no OS-level agent required.
                </Typography>
              </StepContent>
            </Step>
            <Step expanded>
              <StepLabel>(Optional) Manage your chat sessions</StepLabel>
              <StepContent>
                <Typography variant="body2">
                  Hover over a session in the left sidebar to reveal <strong>rename</strong> and{" "}
                  <strong>delete</strong> icons. Renaming lets you replace the auto-generated
                  title (taken from your first message) with something clearer; deleting a
                  session permanently removes it and all of its messages.
                </Typography>
              </StepContent>
            </Step>
            <Step expanded>
              <StepLabel>(Optional) Upload docs for better business-meaning answers</StepLabel>
              <StepContent>
                <Typography variant="body2">
                  Click <strong>Uploads</strong> in the chat toolbar to give the Documentation
                  Agent extra context: a <code>.sql</code> schema file, a <code>.txt</code> notes
                  file, or an image (ER diagram / schema screenshot in <code>.png</code>,{" "}
                  <code>.jpg</code>, <code>.jpeg</code>, <code>.gif</code>, or <code>.webp</code>).
                  Files are capped at 50MB. Images are automatically described by your currently
                  selected LLM model at upload time, then stored so future questions don't need to
                  re-analyze the image. Once a file's status shows <Chip size="small" label="ready" color="success" />,
                  the chatbot will use it automatically for relevant business-meaning questions.
                </Typography>
              </StepContent>
            </Step>
          </Stepper>
        </SectionCard>
      </TabPanel>

      {/* What the Chatbot Can Do */}
      <TabPanel value={tab} index={2}>
        <Grid container spacing={2}>
          <Grid size={{ xs: 12 }}>
            <Alert severity="info">
              Natural language is converted into real SQL behind the scenes — you don't need to
              remember exact SQL syntax, but the agent always shows you the generated statement
              before/while it runs so you can verify what happened.
            </Alert>
          </Grid>
          <Grid size={{ xs: 12 }}>
            <TableContainer component={Paper} variant="outlined">
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell><strong>Capability</strong></TableCell>
                    <TableCell><strong>What you can ask</strong></TableCell>
                    <TableCell><strong>What happens</strong></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  <TableRow>
                    <TableCell>Explore schema</TableCell>
                    <TableCell>"List all tables", "Describe the orders table"</TableCell>
                    <TableCell>Lists schemas/tables/columns, types, keys, and constraints.</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Query data (DQL)</TableCell>
                    <TableCell>"Show me the top 10 customers by total spend"</TableCell>
                    <TableCell>Generates and runs a <code>SELECT</code>, returns results as a table.</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Modify data (DML)</TableCell>
                    <TableCell>"Update all pending orders older than 30 days to cancelled"</TableCell>
                    <TableCell>
                      Generates and executes <code>INSERT</code>/<code>UPDATE</code>/<code>DELETE</code>,
                      reports rows affected. Destructive statements are flagged as irreversible.
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Change schema (DDL)</TableCell>
                    <TableCell>"Create a table named invoices with id, customer_id, amount"</TableCell>
                    <TableCell>
                      Generates and executes <code>CREATE</code>/<code>ALTER</code>/<code>DROP</code>/
                      <code>TRUNCATE</code> statements.
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Explain plan</TableCell>
                    <TableCell>"Explain how this query runs", "Why is this slow?"</TableCell>
                    <TableCell>
                      Runs <code>EXPLAIN (ANALYZE)</code> and translates the plan into plain
                      English (scan types, joins, sorts, timings).
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Optimize a query</TableCell>
                    <TableCell>"Optimize this query", "How can I make this faster?"</TableCell>
                    <TableCell>
                      Analyzes the plan + existing indexes and suggests concrete{" "}
                      <code>CREATE INDEX</code> statements and rewrites (never applied
                      automatically).
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Query timing</TableCell>
                    <TableCell>"How long does this query take?"</TableCell>
                    <TableCell>Executes and reports concrete measured execution time.</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Export results</TableCell>
                    <TableCell>"Export this as CSV", "Download all orders from last month as JSON"</TableCell>
                    <TableCell>
                      Runs the (read-only) query and replies with a download link to a CSV or
                      JSON file, valid for 1 hour, containing up to 50,000 rows.
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Generate an ER diagram</TableCell>
                    <TableCell>"Give me an ER diagram for the public schema", "Show me a diagram of tables orders, customers, products"</TableCell>
                    <TableCell>
                      Renders a visual entity-relationship diagram (tables, columns, primary/
                      foreign keys) as a PNG image shown inline in the chat, with a direct
                      download link for the full-resolution file.
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Get an object's DDL / definition</TableCell>
                    <TableCell>"Give me the DDL for table customers", "Show me the definition of procedure add_two_nums", "Create query for the orders_view view"</TableCell>
                    <TableCell>
                      Looks up and returns the exact <code>CREATE</code> statement for a table,
                      view, materialized view, function, procedure, trigger, sequence, or index —
                      searching every schema/object type automatically if you don't specify one,
                      and showing all matches if the name exists more than once (e.g. an
                      overloaded function).
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Business meaning / documentation</TableCell>
                    <TableCell>
                      "What is the customers table used for?", "What does the status column
                      mean?", "Summarize the ER diagram I uploaded"
                    </TableCell>
                    <TableCell>
                      Combines live PostgreSQL table/column comments with any <code>.sql</code>{" "}
                      files or images you've uploaded (via the <strong>Uploads</strong> button in
                      chat) to answer in plain English, noting if the two sources disagree.
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>General PostgreSQL / how-to questions</TableCell>
                    <TableCell>"What's the difference between a CTE and a subquery?"</TableCell>
                    <TableCell>Answered directly by the Documentation Agent using general PostgreSQL knowledge.</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>
          </Grid>

          <Grid size={{ xs: 12 }}>
            <SectionCard icon={<DownloadIcon color="primary" />} title="Exporting query results (CSV / JSON)">
              <Typography variant="body2" paragraph>
                Ask the chatbot to export a query's full result set as a downloadable file
                instead of just showing it inline in the chat:
              </Typography>
              <Box component="ul" sx={{ pl: 2, m: 0 }}>
                <li>
                  <Typography variant="body2">
                    <strong>Try:</strong> "Export the top 100 customers by spend as CSV" or
                    "Download all orders from last month as JSON".
                  </Typography>
                </li>
                <li>
                  <Typography variant="body2">
                    Only works for read-only <code>SELECT</code>/<code>WITH</code> queries — to
                    export the effect of a DDL/DML change, run that first, then ask to export a
                    follow-up <code>SELECT</code> of the result.
                  </Typography>
                </li>
                <li>
                  <Typography variant="body2">
                    The reply includes a direct download link and the exported row count — up
                    to 50,000 rows per file, higher than the normal in-chat preview limit.
                  </Typography>
                </li>
                <li>
                  <Typography variant="body2">
                    Download links expire after <strong>1 hour</strong>, after which the file is
                    deleted from the server.
                  </Typography>
                </li>
              </Box>
            </SectionCard>
          </Grid>

          <Grid size={{ xs: 12 }}>
            <SectionCard icon={<UploadFileIcon color="primary" />} title="Uploading docs for extra context (RAG)">
              <Typography variant="body2" paragraph>
                Click the <strong>Uploads</strong> button in the chat toolbar (per database
                connection) to add supporting material the Documentation Agent can search:
              </Typography>
              <Box component="ul" sx={{ pl: 2, m: 0 }}>
                <li>
                  <Typography variant="body2">
                    <strong>Allowed file types:</strong> <code>.sql</code>, <code>.txt</code>,{" "}
                    <code>.png</code>, <code>.jpg</code>, <code>.jpeg</code>, <code>.gif</code>,{" "}
                    <code>.webp</code>. Any other file type is rejected.
                  </Typography>
                </li>
                <li>
                  <Typography variant="body2">
                    <strong>Max file size:</strong> 50MB per file.
                  </Typography>
                </li>
                <li>
                  <Typography variant="body2">
                    <strong>.sql files</strong> are read as-is (great for pasting in full schema
                    dumps with <code>CREATE TABLE</code>/<code>COMMENT ON</code> statements).
                  </Typography>
                </li>
                <li>
                  <Typography variant="body2">
                    <strong>Images</strong> (ER diagrams, schema screenshots) are described once by
                    your selected LLM model at upload time — that description is stored so later
                    questions don't re-run image analysis.
                  </Typography>
                </li>
                <li>
                  <Typography variant="body2">
                    Uploaded content is scoped to that one database connection and stored in a
                    separate, dedicated vector store — it never overwrites or replaces the live
                    schema/comment lookups, it only supplements them.
                  </Typography>
                </li>
                <li>
                  <Typography variant="body2">
                    You can remove an uploaded file at any time from the same Uploads dialog.
                  </Typography>
                </li>
              </Box>
            </SectionCard>
          </Grid>
        </Grid>
      </TabPanel>

      {/* Writing Good Prompts */}
      <TabPanel value={tab} index={3}>
        <Grid container spacing={2}>
          <Grid size={{ xs: 12, md: 6 }}>
            <SectionCard icon={<CodeIcon color="primary" />} title="You don't need to know SQL syntax">
              <Typography variant="body2" paragraph>
                The whole point of this chatbot is that natural language gets converted to SQL for
                you. You don't need to remember exact keywords, join syntax, or PostgreSQL-specific
                functions — just describe your intent clearly.
              </Typography>
              <Typography variant="subtitle2">Good examples</Typography>
              <Box component="ul" sx={{ pl: 2, m: 0 }}>
                <li><Typography variant="body2">"Show total sales per month for 2024"</Typography></li>
                <li><Typography variant="body2">"Which customers haven't ordered in 90 days?"</Typography></li>
                <li><Typography variant="body2">"Add a column called status (text) to the orders table"</Typography></li>
                <li><Typography variant="body2">"Delete test users with email like %@test.com"</Typography></li>
                <li><Typography variant="body2">"Give me an ER diagram for the public schema"</Typography></li>
                <li><Typography variant="body2">"Show me the DDL for table customers"</Typography></li>
              </Box>
            </SectionCard>
          </Grid>
          <Grid size={{ xs: 12, md: 6 }}>
            <SectionCard icon={<TipsAndUpdatesIcon color="primary" />} title="Tips for better results">
              <Box component="ul" sx={{ pl: 2, m: 0 }}>
                <li><Typography variant="body2">Name the table/column if you know it — the agent still verifies it exists before using it.</Typography></li>
                <li><Typography variant="body2">Be specific about filters ("last 30 days", "status = 'active'") rather than vague terms.</Typography></li>
                <li><Typography variant="body2">Ask follow-ups in the same session ("now group that by region") — conversation context is kept per database session.</Typography></li>
                <li><Typography variant="body2">If unsure of the schema first, just ask "what tables do I have?" before writing a complex query.</Typography></li>
                <li><Typography variant="body2">For destructive changes, mention scope explicitly (e.g. "only rows where...") to avoid accidentally affecting the whole table.</Typography></li>
                <li><Typography variant="body2">For business-meaning questions ("what is this table for?"), upload a <code>.sql</code> file or ER diagram image via the <strong>Uploads</strong> button so the agent has more to go on than table/column names alone.</Typography></li>
                <li><Typography variant="body2">If you just want to know an object's exact definition (not what it's for), ask for its "DDL" or "definition" instead — you'll get the real <code>CREATE</code> statement, not a plain-English summary.</Typography></li>
              </Box>
            </SectionCard>
          </Grid>
        </Grid>
      </TabPanel>

      {/* Query Optimization */}
      <TabPanel value={tab} index={4}>
        <SectionCard icon={<SpeedIcon color="primary" />} title="How to optimize queries using the chatbot">
          <Typography variant="body2" paragraph>
            The optimization workflow combines the <strong>Explain Plan</strong> and{" "}
            <strong>Optimization</strong> agents so you can go from "this feels slow" to a
            concrete fix without leaving the chat.
          </Typography>
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="subtitle1">1. Ask to explain the query first</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Typography variant="body2">
                Try: <em>"Explain the plan for: SELECT * FROM orders WHERE customer_id = 42"</em>.
                You'll get the raw <code>EXPLAIN</code> output plus a plain-English walkthrough of
                scan types, joins, and sorts — real numbers only, never fabricated.
              </Typography>
            </AccordionDetails>
          </Accordion>
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="subtitle1">2. Ask for optimization suggestions</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Typography variant="body2">
                Try: <em>"Optimize this query"</em> or <em>"How can I make this faster?"</em>. The
                agent checks existing indexes first (so it won't suggest one that already exists),
                looks at <code>pg_stat_statements</code> history when available, and returns a
                bulleted list of concrete suggestions with an exact <code>CREATE INDEX ...</code>{" "}
                statement when relevant.
              </Typography>
            </AccordionDetails>
          </Accordion>
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="subtitle1">3. Review before applying</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Typography variant="body2">
                Suggested indexes/rewrites are <strong>not</strong> applied automatically. Review
                the suggestion, then explicitly ask the chatbot to run it (e.g. "go ahead and
                create that index") if you want it applied via the SQL agent.
              </Typography>
            </AccordionDetails>
          </Accordion>
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="subtitle1">4. Measure the improvement</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Typography variant="body2">
                Ask <em>"How long does this query take now?"</em> before and after applying a
                change to get a concrete before/after timing comparison.
              </Typography>
            </AccordionDetails>
          </Accordion>
        </SectionCard>
      </TabPanel>

      {/* Safety & Best Practices */}
      <TabPanel value={tab} index={5}>
        <Grid container spacing={2}>
          <Grid size={{ xs: 12, md: 6 }}>
            <SectionCard icon={<SecurityIcon color="primary" />} title="Safety notes">
              <Box component="ul" sx={{ pl: 2, m: 0 }}>
                <li><Typography variant="body2">DDL/DML statements run immediately once you ask for them — there is no extra confirmation prompt, so review the generated SQL shown in the chat.</Typography></li>
                <li><Typography variant="body2">Irreversible actions (<code>DROP</code>, <code>TRUNCATE</code>, <code>DELETE</code> without a <code>WHERE</code>) are explicitly flagged in the reply.</Typography></li>
                <li><Typography variant="body2">Database passwords are encrypted at rest and are never echoed back in the UI or chat.</Typography></li>
                <li><Typography variant="body2">Removing a database connection from the Databases tab only deletes the saved connection — it does not touch the actual database or its data.</Typography></li>
              </Box>
            </SectionCard>
          </Grid>
          <Grid size={{ xs: 12, md: 6 }}>
            <SectionCard icon={<TipsAndUpdatesIcon color="primary" />} title="Best practices">
              <Box component="ul" sx={{ pl: 2, m: 0 }}>
                <li><Typography variant="body2">Point this tool at a non-production/staging database while you're first getting familiar with it.</Typography></li>
                <li><Typography variant="body2">Use narrow, explicit filters for updates/deletes rather than broad natural-language requests.</Typography></li>
                <li><Typography variant="body2">Use the Explain Plan / Optimization agents before running expensive queries against large tables.</Typography></li>
                <li><Typography variant="body2">Keep an eye on the database card's health metrics (cache hit ratio, active connections) if things feel slow.</Typography></li>
              </Box>
            </SectionCard>
          </Grid>
        </Grid>
      </TabPanel>

      {/* FAQ */}
      <TabPanel value={tab} index={6}>
        <SectionCard icon={<HelpOutlineIcon color="primary" />} title="Frequently asked questions">
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="subtitle1">Do I need to know SQL to use this?</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Typography variant="body2">
                No. Natural language requests are converted to SQL automatically. Knowing SQL
                helps you double-check the generated statements, but it isn't required.
              </Typography>
            </AccordionDetails>
          </Accordion>
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="subtitle1">Why is the chat input disabled?</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Typography variant="body2">
                You need at least one LLM model configured under the LLM Models tab. Without one,
                there's no model available to power the agents, so the input stays disabled until
                you add one.
              </Typography>
            </AccordionDetails>
          </Accordion>
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="subtitle1">Can I connect more than one database?</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Typography variant="body2">
                Yes. Each imported database gets its own card on the Databases page and its own
                independent chat sessions.
              </Typography>
            </AccordionDetails>
          </Accordion>
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="subtitle1">What do the health metrics on a database card mean?</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Typography variant="body2">
                They're approximate values derived purely from PostgreSQL's own statistics views
                (<code>pg_stat_database</code>, <code>pg_stat_bgwriter</code>/
                <code>pg_stat_checkpointer</code>, <code>pg_stat_activity</code>) — no OS-level
                monitoring agent is installed on your database server.
              </Typography>
            </AccordionDetails>
          </Accordion>
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="subtitle1">What happens if I ask something unrelated to my database?</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Typography variant="body2">
                The fallback agent will politely redirect you, since this chatbot is scoped
                specifically to helping you work with your connected PostgreSQL database.
              </Typography>
            </AccordionDetails>
          </Accordion>
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="subtitle1">What file types can I upload, and how large can they be?</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Typography variant="body2">
                <code>.sql</code>, <code>.txt</code>, <code>.png</code>, <code>.jpg</code>,{" "}
                <code>.jpeg</code>, <code>.gif</code>, and <code>.webp</code> — any other file type
                is rejected. The size limit is 50MB per file. Upload from the{" "}
                <strong>Uploads</strong> button in the chat toolbar.
              </Typography>
            </AccordionDetails>
          </Accordion>
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="subtitle1">How does the chatbot use my uploaded files?</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Typography variant="body2">
                Uploaded <code>.sql</code>/<code>.txt</code> content and image descriptions are
                split into chunks, embedded, and stored in a dedicated vector store scoped to that
                database connection. When you ask a business-meaning question, the Documentation
                Agent searches both this store and your database's live table/column comments,
                and combines both — flagging it if they disagree.
              </Typography>
            </AccordionDetails>
          </Accordion>
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="subtitle1">How long is my chat history kept?</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Typography variant="body2">
                By default 30 days. You can change this from the <strong>Settings</strong> page
                (1–60 days) — messages older than your configured window are automatically deleted
                and are no longer used as conversation context.
              </Typography>
            </AccordionDetails>
          </Accordion>
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="subtitle1">Can I export query results to a file?</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Typography variant="body2">
                Yes — just ask, e.g. "export this as CSV" or "download these results as JSON".
                The chatbot runs the query and replies with a download link (valid for 1 hour,
                up to 50,000 rows) instead of only showing the results inline. Only read-only
                <code> SELECT</code>/<code>WITH</code> queries can be exported directly.
              </Typography>
            </AccordionDetails>
          </Accordion>
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="subtitle1">Can I rename or delete a chat session?</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Typography variant="body2">
                Yes. Hover over any session in the sidebar to reveal edit and delete icons —
                renaming replaces the auto-generated title (from your first message) with your
                own, and deleting permanently removes that session and its messages.
              </Typography>
            </AccordionDetails>
          </Accordion>
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="subtitle1">How many chat sessions are kept per database?</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Typography variant="body2">
                By default 15 per database connection. You can change this from the{" "}
                <strong>Settings</strong> page (1–20) — once you start a new chat beyond that
                limit, your oldest session for that database (by last activity) is automatically
                deleted, similar to how ChatGPT drops old chats once you hit a cap.
              </Typography>
            </AccordionDetails>
          </Accordion>
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="subtitle1">Can I generate an ER diagram of my tables?</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Typography variant="body2">
                Yes — ask something like "give me an ER diagram for the public schema" or "show
                me a diagram of tables orders, customers, and products". The chatbot renders a
                PNG image inline (boxes for tables, columns, primary/foreign key markers, and
                relationship arrows) plus a direct download link for the full-size file.
              </Typography>
            </AccordionDetails>
          </Accordion>
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="subtitle1">Can I get the DDL/create statement for a table, view, or function?</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Typography variant="body2">
                Yes — ask for the "DDL", "definition", "create query", or "create statement" of
                any table, view, materialized view, function, procedure, trigger, sequence, or
                index (e.g. "show me the definition of procedure add_two_nums"). You don't need
                to specify the schema or object type — the chatbot searches everything and shows
                all matches, clearly labeled, if the same name exists in more than one place.
              </Typography>
            </AccordionDetails>
          </Accordion>
        </SectionCard>
      </TabPanel>

      <Divider sx={{ my: 4 }} />
      <Box display="flex" alignItems="center" gap={1} mb={4}>
        <SmartToyIcon color="disabled" />
        <Typography variant="caption" color="text.secondary">
          Powered by a multi-agent LLM orchestrator running on top of your PostgreSQL connections.
        </Typography>
      </Box>
    </Box>
  );
}
