import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { fetchAnalyses } from '@/api/analyses';
import { PageHeader } from '@/components/layout/PageHeader';
import { EmptyState } from '@/components/layout/EmptyState';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { formatRelative } from '@/utils/format';

export function HistoryPage() {
  const { data: analyses = [] } = useQuery({ queryKey: ['analyses'], queryFn: fetchAnalyses });
  const [query, setQuery] = useState('');
  const [status, setStatus] = useState('all');
  const [uploader, setUploader] = useState('all');

  const uploaders = useMemo(() => ['all', ...Array.from(new Set(analyses.map((analysis) => analysis.uploader)))], [analyses]);
  const filtered = analyses.filter((analysis) => {
    const matchesQuery = `${analysis.fileName} ${analysis.uploader}`.toLowerCase().includes(query.toLowerCase());
    const matchesStatus = status === 'all' || analysis.status === status;
    const matchesUploader = uploader === 'all' || analysis.uploader === uploader;
    return matchesQuery && matchesStatus && matchesUploader;
  });

  return (
    <div className="space-y-6">
      <PageHeader title="History" description="Search, filter, and review past analyses." />
      <Card>
        <CardContent className="grid gap-3 p-4 md:grid-cols-3">
          <Input placeholder="Search analyses" value={query} onChange={(event) => setQuery(event.target.value)} />
          <Select value={status} onChange={(event) => setStatus(event.target.value)}>
            <option value="all">All statuses</option>
            <option value="queued">Queued</option>
            <option value="processing">Processing</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
          </Select>
          <Select value={uploader} onChange={(event) => setUploader(event.target.value)}>
            {uploaders.map((value) => (
              <option key={value} value={value}>
                {value === 'all' ? 'All uploaders' : value}
              </option>
            ))}
          </Select>
        </CardContent>
      </Card>
      {analyses.length === 0 ? (
        <EmptyState title="No analyses yet" description="Start by uploading an X-ray to create history records." action={<Button asChild><Link to="/upload">Upload X-ray</Link></Button>} />
      ) : filtered.length === 0 ? (
        <EmptyState title="No results match your filters" description="Try widening your search or resetting the filters." action={<Button variant="outline" onClick={() => { setQuery(''); setStatus('all'); setUploader('all'); }}>Reset filters</Button>} />
      ) : (
        <Card>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>File</TableHead>
                  <TableHead>Uploader</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead />
                </TableRow>
              </TableHeader>
              <TableBody>
                {filtered.map((analysis) => (
                  <TableRow key={analysis.id}>
                    <TableCell className="font-medium">{analysis.fileName}</TableCell>
                    <TableCell>{analysis.uploader}</TableCell>
                    <TableCell>
                      <Badge variant={analysis.status === 'completed' ? 'success' : analysis.status === 'failed' ? 'destructive' : 'secondary'} className="capitalize">
                        {analysis.status.replace('_', ' ')}
                      </Badge>
                    </TableCell>
                    <TableCell>{formatRelative(analysis.createdAt)}</TableCell>
                    <TableCell>
                      <Button variant="outline" size="sm" asChild>
                        <Link to={`/results/${analysis.id}`}>Open</Link>
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
