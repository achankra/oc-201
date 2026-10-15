# Lab 5: a ComponentType and a Trait

This lab works only with OpenChoreo objects, so the folder holds only this README. The workbook steps write their files here:

| File | Written in | What it is |
|---|---|---|
| `service-governed.yaml` | steps 2 and 3 | The built-in `service` ClusterComponentType, exported, renamed `service-governed` and limited to two allowed traits |
| `lab5-scaffold.yaml` | step 5 | What `occ component scaffold` generates against your type |
| `lab5-component.yaml` | step 6 | The greeter sample, renamed `lab5-greeter` and pointed at `deployment/service-governed` |

The files are generated on your cluster, so `.gitignore` leaves them out. Every Lab 5 block in the workbook starts with `cd ~/oc-201-labs/lab5`.

Step 7 applies `../lab7-sre-agent/manifests/notification-channel-webhook.yaml` before it attaches the alert-rule trait, because the trait will not render without a notification channel.
