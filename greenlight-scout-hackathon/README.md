# Greenlight Scout

Greenlight Scout is an evidence-first pre-production research tool for film crews.

It helps production teams research filming requirements for a scene, check current web evidence, separate verified findings from items that still need confirmation, and record a human Greenlight decision.

## Live demo

Frontend:

https://greenlight-scout.web.app

Backend API:

https://greenlight-scout-api-1013782334279.asia-south1.run.app

Swagger:

https://greenlight-scout-api-1013782334279.asia-south1.run.app/docs

## The problem

Pre-production research is usually spread across many sources.

A single scene may involve:

- drone restrictions
- road closures
- night filming
- simulated police vehicles
- background actors
- local permits
- different authorities depending on the exact location

Finding information is only part of the problem.

The production team also needs to understand:

- whether the source is authoritative
- whether the rule actually applies to the requested location
- whether the evidence directly supports the claim
- what still needs confirmation from a human or authority

Greenlight Scout was built to make that process easier to review.

## What Greenlight Scout does

The user enters:

- filming location
- scene description
- production requirements

For example:

```text
Location:
Central London

Scene:
Exterior night scene in Central London.

Requirements:
drone establishing shot
temporary road closure
simulated police vehicle
25 background actors
