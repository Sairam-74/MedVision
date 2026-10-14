import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import {
  createPatient,
  createStudy,
  patients,
  errorMessage,
} from '@/api/workflow';
import { PageHeader } from '@/components/layout/PageHeader';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
export function StudyIntake() {
  const navigate = useNavigate();
  const [search, setSearch] = useState('');
  const [selected, setSelected] = useState('');
  const [name, setName] = useState('');
  const [identifier, setIdentifier] = useState('');
  const [age, setAge] = useState('');
  const [gender, setGender] = useState('Not specified');
  const [date, setDate] = useState('');
  const [body, setBody] = useState('');
  const [laterality, setLaterality] = useState('Not applicable');
  const [history, setHistory] = useState('');
  const [physician, setPhysician] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const query = useQuery({
    queryKey: ['patients', search],
    queryFn: () => patients(search),
  });
  function select(id: string) {
    setSelected(id);
    const patient = query.data?.find((p) => p.id === id);
    if (patient) {
      setName(patient.name);
      setIdentifier(patient.identifier);
      setAge(patient.age === null ? '' : String(patient.age));
      setGender(patient.gender);
    } else {
      setName('');
      setIdentifier('');
      setAge('');
      setGender('Not specified');
    }
  }
  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError('');
    try {
      let patientId = selected;
      if (!patientId) {
        const p = await createPatient({
          name,
          identifier,
          age: age ? Number(age) : null,
          gender,
        });
        patientId = p.id;
        setSelected(p.id);
        setIdentifier(p.identifier);
      }
      const study = await createStudy({
        patient_id: patientId,
        examination_date: date,
        body_part: body,
        laterality,
        clinical_history: history,
        referring_physician: physician,
      });
      navigate(`/studies/${study.id}`);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="space-y-6">
      <PageHeader
        title="Patient and study intake"
        description="Record a synthetic or de-identified research patient before uploading AP, lateral and oblique views."
      />
      <form onSubmit={submit} className="space-y-5 rounded-xl border p-5">
        <label>
          Find returning patient by name or identifier
          <Input
            aria-label="Find returning patient"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </label>
        {query.isError && (
          <p role="alert">
            Patient search failed. Retry before creating a duplicate.
          </p>
        )}
        <label>
          Select existing patient
          <select
            aria-label="Existing patient"
            className="block w-full"
            value={selected}
            onChange={(e) => select(e.target.value)}
          >
            <option value="">Create a new patient</option>
            {query.data?.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name} · {p.identifier} · Age {p.age ?? 'unavailable'} ·{' '}
                {p.gender}
              </option>
            ))}
          </select>
        </label>
        <div className="grid gap-4 md:grid-cols-2">
          <label>
            Patient name
            <Input
              aria-label="Patient name"
              required
              maxLength={120}
              disabled={Boolean(selected)}
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </label>
          <label>
            Patient identifier
            <Input
              aria-label="Patient identifier"
              disabled={Boolean(selected)}
              maxLength={80}
              placeholder="Assigned persistently by server if blank"
              value={identifier}
              onChange={(e) => setIdentifier(e.target.value)}
            />
          </label>
          <label>
            Age
            <Input
              aria-label="Age"
              type="number"
              min={0}
              max={130}
              disabled={Boolean(selected)}
              value={age}
              onChange={(e) => setAge(e.target.value)}
            />
          </label>
          <label>
            Gender
            <select
              aria-label="Gender"
              disabled={Boolean(selected)}
              className="block w-full"
              value={gender}
              onChange={(e) => setGender(e.target.value)}
            >
              {['Not specified', 'Female', 'Male', 'Other'].map((g) => (
                <option key={g}>{g}</option>
              ))}
            </select>
          </label>
          <label>
            Examination date
            <Input
              aria-label="Examination date"
              required
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
            />
          </label>
          <label>
            Body part
            <Input
              aria-label="Body part"
              required
              maxLength={80}
              value={body}
              onChange={(e) => setBody(e.target.value)}
            />
          </label>
          <label>
            Laterality
            <select
              aria-label="Laterality"
              className="block w-full"
              value={laterality}
              onChange={(e) => setLaterality(e.target.value)}
            >
              {['Not applicable', 'Left', 'Right', 'Bilateral'].map((l) => (
                <option key={l}>{l}</option>
              ))}
            </select>
          </label>
          <label>
            Referring physician
            <Input
              aria-label="Referring physician"
              maxLength={120}
              value={physician}
              onChange={(e) => setPhysician(e.target.value)}
            />
          </label>
        </div>
        <label>
          Clinical history / reason
          <textarea
            aria-label="Clinical history"
            className="block w-full rounded border p-2"
            maxLength={4000}
            value={history}
            onChange={(e) => setHistory(e.target.value)}
          />
        </label>
        {error && <p role="alert">{error}</p>}
        <Button disabled={busy || query.isError}>
          {busy ? 'Saving…' : 'Save study and upload views'}
        </Button>
      </form>
      <p>
        Research prototype; AI drafts require qualified review. Do not enter
        identifiable patient information in this local demo.
      </p>
    </div>
  );
}
