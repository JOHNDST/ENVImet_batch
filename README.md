# ENVImet_batch
Sequential multi‑scenario runner for ENVI‑met simulations

## Usage

> **Prerequisite:** You must have a valid ENVI‑met license to run the console.

1. **Prepare a new workspace**  
   - Copy or move your ENVI‑met workspace to a clean folder containing exactly one project.

2. **Gather your scenarios**  
   - Place all `.inx` scenario files into the project folder.  
   - Rename each to the format `sample_{id}.inx` (e.g. `sample_1.inx`, `sample_2.inx`, …).  
   - Ensure there is exactly one `.simx` file in the same project folder.

3. **Launch the batch runner**  
   - Open `envimet_batch.exe`.

4. **Configure inputs**  
   - **Workspace:** Browse to your project folder from step 1.  
   - **Output directory:** Choose where you’d like all results and logs to be saved.  
   - **ENVI‑met core exe:** Browse to `envicore_console.exe` in your ENVI‑met installation.

5. **Set simulation parameters**  
   - **Duration:** Specify the total simulation length (this will apply to every scenario).  
   - **Sample ID or range:**  
     - Tick the simulate all samples to run all samples in your project.
     - Enter a single ID (e.g. `7`) to run only `sample_7.inx`.  
     - Enter a range (e.g. `4-7`) to run `sample_4.inx` through `sample_7.inx`.

6. **Run**  
   - Click **Run Simulation**.  
   - The tool will sequentially invoke ENVI‑met console runs for each selected sample.

7. **Results**  
   - When complete, you'll find each scenario’s output files in your chosen **Output directory**.

