# Lab 5: a ComponentType and a Trait

This lab works only with OpenChoreo objects, so the folder holds no scripts. You create the lab's files yourself as you run the workbook steps. Every Lab 5 block starts with `cd ~/oc-201-labs/lab5`.

## Files you create in this lab

These are not in the repository until you run the step that writes them.

| File | Created in | What it is |
|---|---|---|
| `service-governed.yaml` | steps 2 and 3 | The built-in `service` ClusterComponentType, exported, renamed `service-governed` and limited to two allowed traits |
| `lab5-scaffold.yaml` | step 5 | What `occ component scaffold` generates against your type |
| `lab5-component.yaml` | step 6 | The greeter sample, renamed `lab5-greeter` and pointed at `deployment/service-governed` |

Git ignores them, so your own versions never show up as changes.

## Reference copies

`reference/` holds a copy of each file as it came out of a working v1.3.1 run. Use one if a step fails or you fall behind: copy it into place, then carry on from the next step.

```
cd ~/oc-201-labs/lab5
cp reference/service-governed.yaml .
kubectl apply -f service-governed.yaml
```

Compare before you copy: `diff service-governed.yaml reference/service-governed.yaml`. Names and comments may differ slightly from yours. The scaffold copy is a template with `<TODO>` placeholders, so there is nothing to apply.

## Before step 7

Step 7 applies `../lab7-sre-agent/manifests/notification-channel-webhook.yaml` before it attaches the alert-rule trait, because the trait will not render without a notification channel.
