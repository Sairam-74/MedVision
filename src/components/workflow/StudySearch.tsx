import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { searchStudies } from '@/api/workflow';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
export function StudySearch() {
  const [q, setQ] = useState('');
  const [date, setDate] = useState('');
  const [body, setBody] = useState('');
  const [laterality, setLaterality] = useState('');
  const [status, setStatus] = useState('');
  const [offset, setOffset] = useState(0);
  const query = useQuery({
    queryKey: ['study-search', q, date, body, laterality, status, offset],
    queryFn: () =>
      searchStudies({
        q,
        examination_date: date,
        body_part: body,
        laterality,
        status,
        offset,
        limit: 10,
      }),
  });
  const reset = () => setOffset(0);
  return (
    <section className="space-y-3 rounded-xl border p-4">
      <h2 className="text-lg font-bold">Patient and study history</h2>
      <div className="grid gap-3 md:grid-cols-3">
        <label>
          Name or patient identifier
          <Input
            aria-label="Patient history search"
            value={q}
            onChange={(e) => {
              setQ(e.target.value);
              reset();
            }}
          />
        </label>
        <label>
          Examination date
          <Input
            aria-label="History examination date"
            type="date"
            value={date}
            onChange={(e) => {
              setDate(e.target.value);
              reset();
            }}
          />
        </label>
        <label>
          Body part
          <Input
            aria-label="History body part"
            value={body}
            onChange={(e) => {
              setBody(e.target.value);
              reset();
            }}
          />
        </label>
        <label>
          Laterality
          <select
            aria-label="History laterality"
            className="block"
            value={laterality}
            onChange={(e) => {
              setLaterality(e.target.value);
              reset();
            }}
          >
            {['', 'Left', 'Right', 'Bilateral', 'Not applicable'].map((v) => (
              <option key={v} value={v}>
                {v || 'All lateralities'}
              </option>
            ))}
          </select>
        </label>
        <label>
          Study or report status
          <select
            aria-label="History status"
            className="block"
            value={status}
            onChange={(e) => {
              setStatus(e.target.value);
              reset();
            }}
          >
            {[
              '',
              'draft',
              'final',
              'queued',
              'processing',
              'completed',
              'failed',
              'timed_out',
            ].map((v) => (
              <option key={v} value={v}>
                {v || 'All statuses'}
              </option>
            ))}
          </select>
        </label>
      </div>
      {query.isError && (
        <p role="alert">
          Patient history could not be loaded.
          <button onClick={() => query.refetch()}>Retry</button>
        </p>
      )}
      {query.isLoading ? (
        <p>Searching persisted studies…</p>
      ) : (
        <>
          <p>{query.data?.total ?? 0} studies found</p>
          <div className="overflow-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr>
                  {[
                    'Patient',
                    'Identifier',
                    'Examination',
                    'Body part',
                    'Laterality',
                    'Views / analysis status',
                    'Report',
                    'Open',
                  ].map((h) => (
                    <th key={h} className="p-2">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {query.data?.items.map((s) => (
                  <tr key={s.id} className="border-t">
                    <td className="p-2">{s.patient_name}</td>
                    <td>{s.patient_identifier}</td>
                    <td>{s.examination_date}</td>
                    <td>{s.body_part}</td>
                    <td>{s.laterality}</td>
                    <td>
                      {s.images
                        .map((i) => `${i.view_type}: ${i.status}`)
                        .join(', ') || 'No images'}
                    </td>
                    <td>{s.report_status ?? 'Not generated'}</td>
                    <td>
                      <Link className="underline" to={`/studies/${s.id}`}>
                        Open study
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="flex gap-3">
            <Button
              variant="outline"
              disabled={offset === 0}
              onClick={() => setOffset(Math.max(0, offset - 10))}
            >
              Previous
            </Button>
            <Button
              variant="outline"
              disabled={offset + 10 >= (query.data?.total ?? 0)}
              onClick={() => setOffset(offset + 10)}
            >
              Next
            </Button>
          </div>
        </>
      )}
    </section>
  );
}
