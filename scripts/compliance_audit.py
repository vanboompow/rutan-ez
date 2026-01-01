from pathlib import Path
from core.compliance import compliance_tracker, ManufacturingMethod


def run_compliance_audit():
    print("⚖️ Starting FAA Compliance Audit (Phase 4)...")

    # 1. Simulate progress on key tasks
    print("   Recording construction task progress...")

    # Wing tasks
    compliance_tracker.complete_task("wing_cores_left", ManufacturingMethod.BUILDER_CNC)
    compliance_tracker.complete_task(
        "wing_cores_right", ManufacturingMethod.BUILDER_CNC
    )
    compliance_tracker.complete_task(
        "wing_skins_left", ManufacturingMethod.BUILDER_MANUAL
    )
    compliance_tracker.complete_task(
        "wing_skins_right", ManufacturingMethod.BUILDER_MANUAL
    )

    # Canard tasks
    compliance_tracker.complete_task("canard_cores", ManufacturingMethod.BUILDER_CNC)
    compliance_tracker.complete_task("canard_skins", ManufacturingMethod.BUILDER_MANUAL)

    # Assembly tasks
    # (Assuming these are initialized in ComplianceTracker._init_standard_tasks)
    # We might need to check the IDs of other tasks

    # 2. Check status
    total = compliance_tracker.total_credit
    print(f"   ✅ Current Builder Credit: {total:.1%}")
    print("   ✅ Threshold: 51.0%")

    if compliance_tracker.is_compliant:
        print("   ✅ COMPLIANCE STATUS: AMATEUR-BUILT ELIGIBLE")
    else:
        print("   🏗️ COMPLIANCE STATUS: IN-PROGRESS (Currently below 51%)")

    # 3. Generate Report
    print("   Generating FAA Form 8000-38 draft report...")
    report_md = compliance_tracker.generate_report()

    output_dir = Path("output/compliance")
    output_dir.mkdir(parents=True, exist_ok=True)

    report_file = output_dir / "FAA_compliance_audit.md"
    with open(report_file, "w") as f:
        f.write(report_md)

    print(f"   ✅ Report written to: {report_file}")

    # 4. Export JSON
    json_file = compliance_tracker.export_json(output_dir)
    print(f"   ✅ JSON data exported: {json_file}")

    print("\n🎉 Compliance Audit Completed Successfully!")


if __name__ == "__main__":
    run_compliance_audit()
