# Analytics

The [Cal-ITP Benefits application](https://benefits.calitp.org/) uses [Amplitude](https://amplitude.com/) to collect specific user and event data properties to analyze application usage.

## Information not collected

The following user attributes are *not* collected:

- IP address
- Designated Market Area (DMA)

See the [Amplitude analytics code on GitHub](https://github.com/cal-itp/benefits/blob/dev/benefits/core/templates/core/includes/analytics.html#L30).

## User information collected

A combination of default and application-specific custom user properties are collected for each user who visits the [Cal-ITP Benefits](https://benefits.calitp.org/) application.

### Default Amplitude user properties collected

The following attributes are collected from the browser of every user who visits the application, provided the browser does not block the tracking library:

- Platform
- Device type
- Device family
- Country
- City
- Region
- Start version
- Version
- Carrier
- OS: Operating system name and version
- Language
- Library

Read more about each property on the [Amplitude documentation](https://help.amplitude.com/hc/en-us/articles/215562387-Appendix-Amplitude-User-Property-Definitions).

### Custom user properties collected

The following custom user attributes are collected when the user performs specific actions on the application, like selecing an eligibility type or transit agency:

| Custom user property   | Description                        | Example value                                                                                                     |
| ---------------------- | ---------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| `eligibility_types`    | Eligibility type chosen by user    | `[veteran]`                                                                                                       |
| `eligibility_verifier` | Eligibility verifier used by user  | `VA.gov - Veteran (MST)`                                                                                          |
| `referrer`             | URL that the event came from       | [https://benefits.calitp.org/eligibility/start](https://benefits.calitp.org/eligibility/start)                                                                     |
| `referring_domain`     | Domain that the event came from    | `benefits.calitp.org`                                                                                             |
| `transit_agency`       | Agency chosen by the user          | `Monterey-Salinas Transit`                                                                                        |
| `user_agent`           | User's browser agent               | `Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36` |

## Event information collected

Information is collected on key user actions on the app, called events. Read about each event on the [Amplitude event documentation for Benefits](https://data.amplitude.com/public-doc/hdhfmlby2e). Each event is categorized within one of four categories: core, authentication, eligibility or enrollment.

### Core events

These events track when a user clicks on a link on the application.

- changed language
- clicked link
- viewed page

Read more on each of these events on the [Amplitude event documentation for Benefits, filtered by Core](https://data.amplitude.com/public-doc/hdhfmlby2e?categories=id%3D1702329985270%26group%3Dcategories%26type%3DString%26operator%3Dis%26values%255B0%255D%3Dcore%26dateValue%255Btype%255D%3DSINCE).

### Authentication events

These events track the progress of a user going through the authentication process of both signing in and optionally signing out.

- canceled sign in
- finished sign in
- finished sign out
- started sign in
- started sign out

Read more on each of these events on the [Amplitude event documentation for Benefits, filtered by Authentication](https://data.amplitude.com/public-doc/hdhfmlby2e?categories=id%3D1702329910563%26group%3Dcategories%26type%3DString%26operator%3Dis%26values%255B0%255D%3Doauth%26dateValue%255Btype%255D%3DSINCE).

### Eligibility events

These events track the progress of a user choosing an eligibility verifier and completing eligibility verification.

- returned eligibility
- selected eligibility verifier
- started eligibility

Read more on each of these events on the [Amplitude event documentation for Benefits, filtered by Eligibility](https://data.amplitude.com/public-doc/hdhfmlby2e?categories=id%3D1702329975970%26group%3Dcategories%26type%3DString%26operator%3Dis%26values%255B0%255D%3Deligibility%26dateValue%255Btype%255D%3DSINCE).

### Enrollment events

These events track the progress of a user who has successfully verified their eligibility and is enrolling their payment card with the system.

- closed payment connection (e.g. Littlepay)
- returned enrollment
- started payment connection (e.g. Littlepay)

Read more on each of these events on the [Amplitude event documentation for Benefits, filtered by Enrollment](https://data.amplitude.com/public-doc/hdhfmlby2e?categories=id%3D1702329910563%26group%3Dcategories%26type%3DString%26operator%3Dis%26values%255B0%255D%3Denrollment%26dateValue%255Btype%255D%3DSINCE).

## Key metrics

Various key metrics are collected and analyzed, including:

- **Number of users who successfully completed authentication**: Users who `started sign in`, `finished sign in`
- **Number of users who successfully verified eligibility**: Users who completed the above and `selected eligibility verifier`, `started eligibility`, `returned eligibility` with a status of `True`
- **Numbers of users who successfully completed enrollment**: Users who completed all of the above and `started payment connection`, `closed payment connection` and `returned enrollment` with a status of `Success`
