export interface LandingPageIcon {
    file: string,
    role: string,
    min_frequency: number,
    max_frequency: number,
}

export interface RestLandingPageIcons {
    results: LandingPageIcon[];
    next: string | null;
    previous: string | null;
}
